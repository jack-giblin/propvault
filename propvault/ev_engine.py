import requests
from typing import Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# Config
MIN_EV = 0.5
MAX_EV_CAP = 15.0
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba"]  # keep tight for now

PROP_MARKETS = [
    "player_rebounds",
    "player_assists"
]

ONLY_UNDERS = False  # flip to True if you want only unders

# ── Math ─────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def no_vig_probs(over_odds: float, under_odds: float) -> Tuple[float, float]:
    p_over = 1 / american_to_decimal(over_odds)
    p_under = 1 / american_to_decimal(under_odds)
    total = p_over + p_under
    return p_over / total, p_under / total

def calc_ev(prob: float, odds: float) -> float:
    dec = american_to_decimal(odds)
    return (prob * dec - 1) * 100

def fmt_odds(o: float) -> str:
    return f"+{int(o)}" if o > 0 else str(int(o))

# ── Core ─────────────────────────────────────────

def find_ev_bets(api_key: str):
    all_bets = []
    errors = []

    for sport in SPORTS:
        try:
            events = requests.get(
                f"{BASE_URL}/sports/{sport}/events",
                params={"apiKey": api_key},
                timeout=10
            ).json()

            for event in events:
                game = f"{event['away_team']} @ {event['home_team']}"

                odds_data = requests.get(
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

                books = {b['key']: b for b in odds_data.get('bookmakers', [])}

                # REQUIRE BOTH BOOKS
                if SHARP_BOOK not in books or TARGET_BOOK not in books:
                    continue

                pin_markets = books[SHARP_BOOK]['markets']
                nov_markets = books[TARGET_BOOK]['markets']

                for pin_mkt in pin_markets:

                    nov_mkt = next(
                        (m for m in nov_markets if m['key'] == pin_mkt['key']),
                        None
                    )
                    if not nov_mkt:
                        continue

                    # Group Pinnacle by player + point
                    grouped = {}
                    for o in pin_mkt['outcomes']:
                        player = o['description']
                        point = o.get('point')
                        side = o['name']  # Over / Under

                        key = (player, point)

                        if key not in grouped:
                            grouped[key] = {}

                        grouped[key][side] = o

                    # Evaluate props
                    for (player, point), sides in grouped.items():

                        if "Over" not in sides or "Under" not in sides:
                            continue

                        pin_over = sides["Over"]["price"]
                        pin_under = sides["Under"]["price"]

                        fair_over, fair_under = no_vig_probs(pin_over, pin_under)

                        # Match with Novig
                        for n in nov_mkt['outcomes']:

                            if n['description'] != player:
                                continue
                            if n.get('point') != point:
                                continue

                            side = n['name']
                            odds = n['price']

                            if ONLY_UNDERS and side != "Under":
                                continue

                            prob = fair_over if side == "Over" else fair_under
                            ev = calc_ev(prob, odds)

                            if ev < MIN_EV or ev > MAX_EV_CAP:
                                continue

                            all_bets.append({
                                "Sport": "NBA",
                                "Game": game,
                                "Market": pin_mkt['key'].replace("player_", "").replace("_", " ").title(),
                                "Player": player,
                                "Side": f"{side} {point}",
                                "Target Odds": fmt_odds(odds),
                                "Fair Odds": fmt_odds(pin_over if side == "Over" else pin_under),
                                "EV %": round(ev, 2)
                            })

        except Exception as e:
            errors.append(f"{sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
