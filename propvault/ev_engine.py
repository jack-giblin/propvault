import requests
from typing import List, Dict, Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# ── Config ─────────────────────────────────────────────────────────────
MIN_EV = 0.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba"]  # keep stable first (add MLB later if needed)

PROP_MARKETS = [
    "player_rebounds",
    "player_assists",
]

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

# ── Core Engine ────────────────────────────────────────────────────────

def find_ev_bets(api_key: str):
    bets = []
    errors = []

    for sport in SPORTS:
        try:
            events = requests.get(
                f"{BASE_URL}/sports/{sport}/events",
                params={"apiKey": api_key},
                timeout=10
            ).json()

            for event in events:

                odds = requests.get(
                    f"{BASE_URL}/sports/{sport}/events/{event['id']}/odds",
                    params={
                        "apiKey": api_key,
                        "regions": "us,eu",
                        "markets": ",".join(PROP_MARKETS),
                        "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
                        "oddsFormat": "american"
                    },
                    timeout=10
                ).json()

                books = {b["key"]: b for b in odds.get("bookmakers", [])}

                if SHARP_BOOK not in books:
                    continue

                sharp_book = books[SHARP_BOOK]
                target_book = books.get(TARGET_BOOK)

                if not target_book:
                    continue  # no target book → skip safely

                for sharp_market in sharp_book.get("markets", []):
                    target_market = next(
                        (m for m in target_book.get("markets", [])
                         if m["key"] == sharp_market["key"]),
                        None
                    )
                    if not target_market:
                        continue

                    # ── Build lookup maps (robust matching) ──
                    sharp_map = {}
                    for o in sharp_market.get("outcomes", []):
                        key = (o["description"], o.get("point"), o["name"])
                        sharp_map[key] = o

                    target_map = {}
                    for o in target_market.get("outcomes", []):
                        key = (o["description"], o.get("point"), o["name"])
                        target_map[key] = o

                    # ── EV calculation ──
                    for (player, point, side), target_o in target_map.items():

                        opp_side = "Under" if side == "Over" else "Over"
                        key = (player, point, side)
                        opp_key = (player, point, opp_side)

                        if key not in sharp_map or opp_key not in sharp_map:
                            continue

                        sharp_price = sharp_map[key]["price"]
                        sharp_opp = sharp_map[opp_key]["price"]

                        fair_over, fair_under = no_vig_prob(sharp_price, sharp_opp)
                        fair_prob = fair_over if side == "Over" else fair_under

                        if fair_prob < MIN_WIN_PROB:
                            continue

                        ev = (fair_prob * american_to_decimal(target_o["price"]) - 1) * 100

                        if MIN_EV <= ev <= MAX_EV_CAP:
                            bets.append({
                                "Sport": sport.split("_")[1].upper(),
                                "Game": f"{event.get('away_team')} @ {event.get('home_team')}",
                                "Market": sharp_market["key"]
                                    .replace("player_", "")
                                    .replace("_", " ")
                                    .title(),
                                "Player": player,
                                "Side": f"{side} {point}",
                                "Target Odds": fmt_odds(target_o["price"]),
                                "Fair Odds": fmt_odds(sharp_price),
                                "EV %": round(ev, 2)
                            })

        except Exception as e:
            errors.append(f"{sport}: {str(e)}")

    bets.sort(key=lambda x: x["EV %"], reverse=True)
    return bets, errors
