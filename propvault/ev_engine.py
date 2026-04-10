import requests
from typing import List, Dict, Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# ── CONFIG ─────────────────────────────────────────────
MIN_EV = 0.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba", "baseball_mlb"]

PROP_MARKETS = [
    "player_rebounds",
    "player_assists",
    "player_strikeouts"
]

# ── HELPERS ────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1


def no_vig_prob(a: float, b: float) -> Tuple[float, float]:
    pa = 1 / american_to_decimal(a)
    pb = 1 / american_to_decimal(b)
    total = pa + pb
    return pa / total, pb / total


def fmt_odds(o: float) -> str:
    return f"+{int(o)}" if o > 0 else str(int(o))


# ── ENGINE ─────────────────────────────────────────────

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
                event_id = event.get("id")
                if not event_id:
                    continue

                odds = requests.get(
                    f"{BASE_URL}/sports/{sport}/events/{event_id}/odds",
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

                if SHARP_BOOK not in books or TARGET_BOOK not in books:
                    continue

                sharp_markets = books[SHARP_BOOK].get("markets", [])
                target_markets = books[TARGET_BOOK].get("markets", [])

                for sharp_m in sharp_markets:

                    target_m = next(
                        (m for m in target_markets if m["key"] == sharp_m["key"]),
                        None
                    )

                    if not target_m:
                        continue

                    sharp_outcomes = sharp_m.get("outcomes", [])
                    target_outcomes = target_m.get("outcomes", [])

                    # ── BUILD SHARP LOOKUP ──
                    sharp_lookup = {}
                    for o in sharp_outcomes:
                        sharp_lookup[(o["description"], o["name"], o.get("point"))] = o

                    # ── BUILD TARGET LOOKUP ──
                    target_lookup = {}
                    for o in target_outcomes:
                        target_lookup[(o["description"], o["name"], o.get("point"))] = o

                    # ── EV CALC ──
                    for (player, side, point), target_o in target_lookup.items():

                        opp_side = "Under" if side == "Over" else "Over"
                        key = (player, side, point)
                        opp_key = (player, opp_side, point)

                        if key not in sharp_lookup or opp_key not in sharp_lookup:
                            continue

                        sharp_price = sharp_lookup[key]["price"]
                        sharp_opp_price = sharp_lookup[opp_key]["price"]

                        fair_over, fair_under = no_vig_prob(sharp_price, sharp_opp_price)
                        fair_prob = fair_over if side == "Over" else fair_under

                        if fair_prob < MIN_WIN_PROB:
                            continue

                        target_price = target_o["price"]

                        ev = (fair_prob * american_to_decimal(target_price) - 1) * 100

                        if ev < MIN_EV or ev > MAX_EV_CAP:
                            continue

                        bets.append({
                            "Sport": sport.split("_")[1].upper(),
                            "Game": f"{event.get('away_team')} @ {event.get('home_team')}",
                            "Market": sharp_m["key"].replace("player_", "").replace("_", " ").title(),
                            "Player": player,
                            "Side": f"{side} {point}",
                            "Target Odds": fmt_odds(target_price),
                            "Fair Odds": fmt_odds(sharp_price),
                            "EV %": round(ev, 2)
                        })

        except Exception as e:
            errors.append(f"{sport}: {str(e)}")

    bets.sort(key=lambda x: x["EV %"], reverse=True)
    return bets, errors
