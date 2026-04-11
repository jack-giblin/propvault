import requests
import streamlit as st
from datetime import datetime, timezone
from typing import List, Dict, Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# ── Config ─────────────────────────────────────────────────────────────
MIN_EV = 2.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

# Only Under side is evaluated for prop markets
UNDER_ONLY_MARKETS = {"pitcher_strikeouts", "player_assists"}

SPORTS_MARKETS = {
    "basketball_nba": ["totals", "player_assists"],
    "baseball_mlb": ["totals", "pitcher_strikeouts"],
    "icehockey_nhl": ["totals"],
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

# ── Helpers ────────────────────────────────────────────────────────────

def is_upcoming(commence_time_str: str) -> bool:
    try:
        commence = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        return commence > datetime.now(timezone.utc)
    except Exception:
        return False

# ── L5 Stats Lookups ───────────────────────────────────────────────────

def get_nba_l5(player_name: str, stat: str) -> str:
    try:
        search = requests.get(
            "https://www.balldontlie.io/api/v1/players",
            params={"search": player_name, "per_page": 1},
            timeout=8,
        )
        results = search.json().get("data", [])
        if not results:
            return None
        player_id = results[0]["id"]

        logs = requests.get(
            "https://www.balldontlie.io/api/v1/stats",
            params={
                "player_ids[]": player_id,
                "per_page": 5,
                "seasons[]": 2024,
            },
            timeout=8,
        )
        games = logs.json().get("data", [])
        if not games:
            return None

        values = [g.get(stat, 0) for g in games if g.get("min") and g["min"] != "00:00"]
        if not values:
            return None

        avg = sum(values) / len(values)
        return f"{avg:.1f}"
    except Exception:
        return None


def get_mlb_l5_strikeouts(player_name: str) -> str:
    try:
        search = requests.get(
            "https://statsapi.mlb.com/api/v1/people/search",
            params={"names": player_name, "sportId": 1},
            timeout=8,
        )
        people = search.json().get("people", [])
        if not people:
            return None
        player_id = people[0]["id"]

        logs = requests.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats",
            params={
                "stats": "gameLog",
                "group": "pitching",
                "season": 2025,
                "limit": 5,
            },
            timeout=8,
        )
        splits = logs.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return None

        ks = [s["stat"].get("strikeOuts", 0) for s in splits[:5]]
        if not ks:
            return None

        avg = sum(ks) / len(ks)
        return f"{avg:.1f}"
    except Exception:
        return None


def get_player_l5(player_name: str, market_key: str) -> str:
    if market_key == "player_assists":
        val = get_nba_l5(player_name, "ast")
        return f"L5 avg: {val} ast" if val else None
    elif market_key == "pitcher_strikeouts":
        val = get_mlb_l5_strikeouts(player_name)
        return f"L5 avg: {val} K" if val else None
    return None

# ── Core Engine ────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def find_ev_bets(api_key: str):

def find_ev_bets(api_key: str):
    bets = []
    errors = []

    for sport, prop_markets in SPORTS_MARKETS.items():
        try:
            r = requests.get(
                f"{BASE_URL}/sports/{sport}/odds",
                params={
                    "apiKey": api_key,
                    "regions": "us,eu",
                    "markets": ",".join(prop_markets),
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
                    "oddsFormat": "american",
                },
                timeout=15,
            )
            r.raise_for_status()
            events = r.json()

        except Exception as e:
            errors.append(f"{sport} bulk fetch: {str(e)}")
            continue

        for event in events:
            if not is_upcoming(event.get("commence_time", "")):
                continue

            books = {b["key"]: b for b in event.get("bookmakers", [])}

            if SHARP_BOOK not in books or TARGET_BOOK not in books:
                continue

            sharp_book = books[SHARP_BOOK]
            target_book = books[TARGET_BOOK]

            for sharp_market in sharp_book.get("markets", []):
                target_market = next(
                    (m for m in target_book.get("markets", [])
                     if m["key"] == sharp_market["key"]),
                    None,
                )
                if not target_market:
                    continue

                sharp_map = {
                    (o.get("description"), o.get("point"), o["name"]): o
                    for o in sharp_market.get("outcomes", [])
                }
                target_map = {
                    (o.get("description"), o.get("point"), o["name"]): o
                    for o in target_market.get("outcomes", [])
                }

                for (player, point, side), target_o in target_map.items():
                    # Under-only filter for prop markets
                    if sharp_market["key"] in UNDER_ONLY_MARKETS and side != "Under":
                        continue

                    # For totals, only evaluate Unders
                    if sharp_market["key"] == "totals" and side != "Under":
                        continue

                    opp_side = "Over"
                    key = (player, point, side)
                    opp_key = (player, point, opp_side)

                    if key not in sharp_map or opp_key not in sharp_map:
                        continue

                    sharp_price = sharp_map[key]["price"]
                    sharp_opp = sharp_map[opp_key]["price"]

                    fair_over, fair_under = no_vig_prob(sharp_opp, sharp_price)
                    fair_prob = fair_under

                    if fair_prob < MIN_WIN_PROB:
                        continue

                    ev = (fair_prob * american_to_decimal(target_o["price"]) - 1) * 100

                    if MIN_EV <= ev <= MAX_EV_CAP:
                        l5 = get_player_l5(player, sharp_market["key"]) if player else None
                        market_label = (
                            sharp_market["key"]
                            .replace("player_", "")
                            .replace("pitcher_", "")
                            .replace("batter_", "")
                            .replace("_", " ")
                            .title()
                        )
                        game_label = f"{event.get('away_team')} @ {event.get('home_team')}"
                        player_label = player if player else game_label

                        bets.append({
                            "Sport": sport.split("_")[1].upper(),
                            "Game": game_label,
                            "Market": market_label,
                            "Player": player_label,
                            "Side": f"Under {point}",
                            "Target Odds": fmt_odds(target_o["price"]),
                            "Fair Odds": fmt_odds(sharp_price),
                            "Fair Prob": f"{fair_prob:.1%}",
                            "EV %": round(ev, 2),
                            "L5": l5,
                        })

    bets.sort(key=lambda x: x["EV %"], reverse=True)
    return bets, errors
