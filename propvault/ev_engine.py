import requests
from datetime import datetime, timezone
from typing import List, Dict, Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# ── Config ─────────────────────────────────────────────────────────────
MIN_EV = 2.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

UNDER_ONLY_MARKETS = {"pitcher_strikeouts", "player_assists"}

GAME_MARKETS = {
    "basketball_nba": ["totals"],
    "baseball_mlb": ["totals"],
    "icehockey_nhl": ["totals"],
}

PROP_MARKETS = {
    "basketball_nba": ["player_assists"],
    "baseball_mlb": ["pitcher_strikeouts"],
}

# ── Math ───────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def no_vig_prob(a: float, b: float) -> Tuple[float, float]:
    pa = 1 / american_to_decimal(a)
    pb = 1 / american_to_decimal(b)
    s = pa + pb
    return pa / s, pb / s

def fmt_odds(o: float) -> str:
    return f"+{int(o)}" if o > 0 else str(int(o))

def is_upcoming(commence_time_str: str) -> bool:
    try:
        commence = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        return commence > datetime.now(timezone.utc)
    except:
        return False

# ── L5 Stats Lookups ───────────────────────────────────────────────────

def get_mlb_l5_strikeouts(player_name: str) -> str:
    try:
        search = requests.get("https://statsapi.mlb.com/api/v1/people/search", params={"names": player_name, "sportId": 1}, timeout=8)
        people = search.json().get("people", [])
        if not people: return None
        player_id = people[0]["id"]
        logs = requests.get(f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats", params={"stats": "gameLog", "group": "pitching", "season": 2026, "limit": 5}, timeout=8)
        splits = logs.json().get("stats", [{}])[0].get("splits", [])
        if not splits: return None
        ks = [s["stat"].get("strikeOuts", 0) for s in splits[:5]]
        return f"{sum(ks) / len(ks):.1f}" if ks else None
    except: return None

def get_player_l5(player_name: str, market_key: str) -> str:
    if market_key == "player_assists":
        val = get_nba_l5(player_name, "ast")
        return f"L5 avg: {val} ast" if val else None
    elif market_key == "pitcher_strikeouts":
        val = get_mlb_l5_strikeouts(player_name)
        return f"L5 avg: {val} K" if val else None
    return None

# ── Processing Helper ──────────────────────────────────────────────────

def process_logic(events, sport, bets):
    for event in events:
        if not is_upcoming(event.get("commence_time", "")):
            continue
        
        books = {b["key"]: b for b in event.get("bookmakers", [])}
        if SHARP_BOOK not in books or TARGET_BOOK not in books:
            continue

        sharp_book = books[SHARP_BOOK]
        target_book = books[TARGET_BOOK]

        for sharp_market in sharp_book.get("markets", []):
            target_market = next((m for m in target_book.get("markets", []) if m["key"] == sharp_market["key"]), None)
            if not target_market: continue

            sharp_map = {(o.get("description"), o.get("point"), o["name"]): o for o in sharp_market.get("outcomes", [])}
            target_map = {(o.get("description"), o.get("point"), o["name"]): o for o in target_market.get("outcomes", [])}

            for (player, point, side), target_o in target_map.items():
                if (sharp_market["key"] in UNDER_ONLY_MARKETS or sharp_market["key"] == "totals") and side != "Under":
                    continue

                opp_side = "Over"
                key, opp_key = (player, point, side), (player, point, opp_side)
                if key not in sharp_map or opp_key not in sharp_map: continue

                sharp_price, sharp_opp = sharp_map[key]["price"], sharp_map[opp_key]["price"]
                _, fair_prob = no_vig_prob(sharp_opp, sharp_price)
                if fair_prob < MIN_WIN_PROB: continue

                ev = (fair_prob * american_to_decimal(target_o["price"]) - 1) * 100
                if MIN_EV <= ev <= MAX_EV_CAP:
                    l5 = get_player_l5(player, sharp_market["key"]) if player else None
                    market_label = sharp_market["key"].replace("player_", "").replace("pitcher_", "").replace("_", " ").title()
                    bets.append({
                        "Sport": sport.split("_")[1].upper(),
                        "Game": f"{event.get('away_team')} @ {event.get('home_team')}",
                        "Market": market_label,
                        "Player": player if player else "Game Total",
                        "Side": f"Under {point}",
                        "Target Odds": fmt_odds(target_o["price"]),
                        "Fair Odds": fmt_odds(sharp_price),
                        "Fair Prob": f"{fair_prob:.1%}",
                        "EV %": round(ev, 2),
                        "L5": l5,
                    })

# ── Core Engine ────────────────────────────────────────────────────────

def find_ev_bets(api_key: str):
    bets = []
    errors = []

    # 1. TOTALS LOOP
    for sport, markets in GAME_MARKETS.items():
        try:
            r = requests.get(f"{BASE_URL}/sports/{sport}/odds", params={
                "apiKey": api_key, "regions": "us,eu", "markets": ",".join(markets),
                "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"
            }, timeout=15)
            r.raise_for_status()
            process_logic(r.json(), sport, bets)
        except Exception as e:
            errors.append(f"{sport} totals error: {str(e)}")

    # 2. PROPS LOOP
    for sport, markets in PROP_MARKETS.items():
        try:
            e_req = requests.get(f"{BASE_URL}/sports/{sport}/events", params={"apiKey": api_key}, timeout=10)
            e_req.raise_for_status()
            for event_info in e_req.json():
                try:
                    r = requests.get(f"{BASE_URL}/sports/{sport}/events/{event_info['id']}/odds", params={
                        "apiKey": api_key, "regions": "us,eu", "markets": ",".join(markets),
                        "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"
                    }, timeout=10)
                    if r.status_code == 200:
                        process_logic([r.json()], sport, bets)
                except:
                    continue
        except Exception as e:
            errors.append(f"{sport} props error: {str(e)}")

    bets.sort(key=lambda x: x["EV %"], reverse=True)
    return bets, errors
