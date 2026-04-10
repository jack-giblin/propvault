import requests
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

BASE_URL       = "https://api.the-odds-api.com/v4"
MIN_EV         = 2.5
MAX_EV_CAP     = 15.0
MIN_WIN_PROB   = 0.40
SHARP_BOOK     = "pinnacle"
TARGET_BOOK    = "novig"
SPORTS         = ["baseball_mlb", "basketball_nba"]

# Only the markets you specifically asked for
PROP_MARKETS   = [
    "player_rebounds", "player_assists", # NBA
    "player_strikeouts"                  # MLB
]

# ── Math Utilities ────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def no_vig_prob(price_a: float, price_b: float) -> Tuple[float, float]:
    pa, pb = 1 / american_to_decimal(price_a), 1 / american_to_decimal(price_b)
    return pa / (pa + pb), pb / (pa + pb)

def fmt_odds(o: float) -> str:
    return f"+{int(o)}" if o > 0 else str(int(o))

# ── Logic ─────────────────────────────────────────────────────────────────────

def find_ev_bets(api_key: str):
    all_bets, errors = [], []

    for sport in SPORTS:
        try:
            # 1. Fetch Events first to get IDs
            events_resp = requests.get(f"{BASE_URL}/sports/{sport}/events", params={
                "apiKey": api_key
            }, timeout=10).json()

            for event in events_resp:
                game_info = {
                    'sport': sport.split('_')[1].upper(), 
                    'away': event['away_team'], 
                    'home': event['home_team']
                }

                # 2. Fetch Player Props for this specific event
                # CRITICAL: We use 'us,eu' to ensure we get both Novig (US) and Pinnacle (EU)
                prop_resp = requests.get(f"{BASE_URL}/sports/{sport}/events/{event['id']}/odds", params={
                    "apiKey": api_key, 
                    "regions": "us,eu", 
                    "markets": ",".join(PROP_MARKETS),
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", 
                    "oddsFormat": "american"
                }, timeout=10).json()

                books = {bm['key']: bm for bm in prop_resp.get('bookmakers', [])}
                
                # Check if BOTH books exist in the data
                if SHARP_BOOK in books and TARGET_BOOK in books:
                    for p_mkt in books[SHARP_BOOK]['markets']:
                        # Find the same market in Novig
                        nov_mkt = next((m for m in books[TARGET_BOOK]['markets'] if m['key'] == p_mkt['key']), None)
                        if not nov_mkt: continue

                        # Player Props contain many players. We need to group by Player + Side (Over/Under)
                        # We group by (Player Name, Outcome Name, Point)
                        pin_outcomes = {(o['description'], o['name'], o.get('point')): o for o in p_mkt['outcomes']}
                        nov_outcomes = {(o['description'], o['name'], o.get('point')): o for o in nov_mkt['outcomes']}

                        for key, n_outcome in nov_outcomes.items():
                            player_name, side, point = key
                            
                            # Find the OPPOSITE side for the same player at Pinnacle to calculate No-Vig
                            other_side = "Under" if side == "Over" else "Over"
                            opp_key = (player_name, other_side, point)

                            if key in pin_outcomes and opp_key in pin_outcomes:
                                pin_odds = pin_outcomes[key]['price']
                                pin_opp_odds = pin_outcomes[opp_key]['price']
                                
                                # Calculate Fair Probability using Pinnacle's two-sided market
                                fair_prob, _ = no_vig_prob(pin_odds, pin_opp_odds)

                                if fair_prob >= MIN_WIN_PROB:
                                    nov_odds = n_outcome['price']
                                    ev = (fair_prob * american_to_decimal(nov_odds) - 1) * 100

                                    if MIN_EV <= ev <= MAX_EV_CAP:
                                        all_bets.append({
                                            "Sport": game_info['sport'],
                                            "Game": f"{game_info['away']} @ {game_info['home']}",
                                            "Market": p_mkt['key'].replace("player_", "").replace("_", " ").title(),
                                            "Player": player_name,
                                            "Side": f"{side} {point}",
                                            "Target Odds": fmt_odds(nov_odds),
                                            "Fair Odds": fmt_odds(pin_odds),
                                            "EV %": round(ev, 2)
                                        })

        except Exception as e:
            errors.append(f"Error in {sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
