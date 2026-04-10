import requests
from typing import List, Dict, Tuple

BASE_URL = "https://api.the-odds-api.com/v4"

# Config
MIN_EV = 0.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.0  # don't filter too early

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORT = "basketball_nba"  # focus NBA only for now

PROP_MARKETS = [
    "player_rebounds",
    "player_assists"
]

ONLY_UNDERS = False  # flip to True if you want ONLY unders

# ── Math ─────────────────────────────────────────

def american_to_decimal(odds: float) -> float:
    return odds / 100 + 1 if odds > 0 else 100 / abs(odds) + 1

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

# ── Core Engine ──────────────────────────────────

def find_ev_bets(api_key: str):

    all_bets = []
    errors = []

    try:
        events = requests.get(
            f"{BASE_URL}/sports/{SPORT}/events",
            params={"apiKey": api_key},
            timeout=10
        ).json()

        for event in events:

            game = f"{event['away_team']} @ {event['home_team']}"

            odds_data = requests.get(
                f"{BASE_URL}/sports/{SPORT}/events/{event['id']}/odds",
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

            # REQUIRE BOTH BOOKS (your core philosophy)
            if SHARP_BOOK not in books or TARGET_BOOK not in books:
                continue

            pin_markets = books[SHARP_BOOK]['markets']
            nov_markets = books[TARGET_BOOK]['markets']

            # Loop through Pinnacle markets
            for pin_mkt in pin_markets:

                # Find matching market in Novig
                nov_mkt = next(
                    (m for m in nov_markets if m['key'] == pin_mkt['key']),
                    None
                )
                if not nov_mkt:
                    continue

                # Group Pinnacle outcomes by player + point
                grouped = {}

                for o in pin_mkt['outcomes']:
                    player = o['description']
                    point = o.get('point')
                    side = o['name']  # Over / Under

                    key = (player, point)

                    if key not in grouped:
                        grouped[key] = {}

                    grouped[key][side] = o

                # Evaluate each player prop
                for (player, point), sides in grouped.items():

                    if "Over" not in sides or "Under" not in sides:
                        continue

                    pin_over = sides["Over"]['price']
                    pin_under = sides["Under"]['price']

                    fair_over, fair_under = no_vig_probs(pin_over, pin_under)

                    # Now match with Novig
                    for n in nov_mkt['outcomes']:
                        if n['description'] != player:
                            continue
                        if n.get('point') != point:
                            continue

                        side = n['name']
                        odds = n['price']

                        # Optional filter: ONLY UNDERS
                        if ONLY_UNDERS and side != "Under":
                            continue

                        if side == "Over":
                            prob = fair_over
                        else:
                            prob = fair_under

                        ev = calc_ev(prob, odds)

                        if ev < MIN_EV or ev > MAX_EV_CAP:
                            continue

                        if prob < MIN_WIN_PROB:
                            continue

                        all_bets.append({
                            "Game": game,
                            "Market": pin_mkt['key'].replace("player_", "").replace("_", " ").title(),
                            "Player": player,
                            "Side": f"{side} {point}",
                            "Target Odds": fmt_odds(odds),
                            "Fair Odds": fmt_odds(pin_over if side == "Over" else pin_under),
                            "Win Prob": round(prob * 100, 2),
                            "EV %": round(ev, 2)
                        })

    except Exception as e:
        errors.append(str(e))

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)

    return all_bets, errors
