"""
PropVault — EV Engine (Spreads, Totals & Player Props)
Filters: MIN_EV = 2.5, MIN_WIN_PROB = 0.40
"""

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

# Standard Markets & Main Prop Keys
MAIN_MARKETS   = "spreads,totals"
PROP_MARKETS   = [
    "player_points", "player_rebounds", "player_assists", # NBA
    "player_strikeouts", "player_hits", "player_home_runs" # MLB
]

# ── Math Utilities ────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    return f"+{round((d-1)*100)}" if d >= 2 else str(round(-100 / (d-1)))

def no_vig_prob(price_a: float, price_b: float) -> Tuple[float, float]:
    pa, pb = 1 / american_to_decimal(price_a), 1 / american_to_decimal(price_b)
    return pa / (pa + pb), pb / (pa + pb)

def fmt_odds(o: float) -> str:
    return f"+{int(o)}" if o > 0 else str(int(o))

# ── Logic ─────────────────────────────────────────────────────────────────────

def process_market(market: dict, pinnacle_mkt: dict, novig_mkt: dict, game_info: dict):
    """Calculates EV for a specific market outcome."""
    bets = []
    pin_outcomes = {o["name"]: o for o in pinnacle_mkt["outcomes"]}
    nov_outcomes = {o["name"]: o for o in novig_mkt["outcomes"]}

    # Ensure we have 2 sides to calculate no-vig (Over/Under or Team A/B)
    if len(pin_outcomes) != 2: return bets

    sides = list(pin_outcomes.keys())
    try:
        fair_a, fair_b = no_vig_prob(pin_outcomes[sides[0]]["price"], pin_outcomes[sides[1]]["price"])
        fair_map = {sides[0]: fair_a, sides[1]: fair_b}
    except: return bets

    for side, fair_prob in fair_map.items():
        if side not in nov_outcomes or fair_prob < MIN_WIN_PROB:
            continue

        nov_odds = nov_outcomes[side]["price"]
        ev = (fair_prob * american_to_decimal(nov_odds) - 1) * 100

        if MIN_EV <= ev <= MAX_EV_CAP:
            point = nov_outcomes[side].get("point", "")
            bets.append({
                "Sport": game_info['sport'],
                "Game": f"{game_info['away']} @ {game_info['home']}",
                "Market": market.replace("_", " ").title(),
                "Side": f"{side} {point}".strip(),
                "Target Odds": fmt_odds(nov_odds),
                "Fair Prob": f"{fair_prob*100:.1f}%",
                "EV %": round(ev, 2)
            })
    return bets

def find_ev_bets(api_key: str):
    all_bets, errors = [], []
    now = datetime.now(timezone.utc)

    for sport in SPORTS:
        try:
            # 1. Fetch Main Markets (Spreads/Totals)
            resp = requests.get(f"{BASE_URL}/sports/{sport}/odds", params={
                "apiKey": api_key, "regions": "us", "markets": MAIN_MARKETS,
                "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"
            }, timeout=10).json()

            for event in resp:
                # Basic Game Info
                game_info = {'sport': sport.split('_')[1].upper(), 'away': event['away_team'], 'home': event['home_team'], 'id': event['id']}
                
                # Check for Spreads/Totals
                books = {bm['key']: bm for bm in event.get('bookmakers', [])}
                if SHARP_BOOK in books and TARGET_BOOK in books:
                    for m_key in ["spreads", "totals"]:
                        pin_m = next((m for m in books[SHARP_BOOK]['markets'] if m['key'] == m_key), None)
                        nov_m = next((m for m in books[TARGET_BOOK]['markets'] if m['key'] == m_key), None)
                        if pin_m and nov_m:
                            all_bets.extend(process_market(m_key, pin_m, nov_m, game_info))

                # 2. Fetch Player Props for this specific event
                # Note: This increases API usage. Remove if you only want game lines.
                prop_resp = requests.get(f"{BASE_URL}/sports/{sport}/events/{event['id']}/odds", params={
                    "apiKey": api_key, "regions": "us", "markets": ",".join(PROP_MARKETS),
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"
                }, timeout=10).json()

                prop_books = {bm['key']: bm for bm in prop_resp.get('bookmakers', [])}
                if SHARP_BOOK in prop_books and TARGET_BOOK in prop_books:
                    for p_mkt in prop_books[SHARP_BOOK]['markets']:
                        nov_p_mkt = next((m for m in prop_books[TARGET_BOOK]['markets'] if m['key'] == p_mkt['key']), None)
                        if nov_p_mkt:
                            all_bets.extend(process_market(p_mkt['key'], p_mkt, nov_p_mkt, game_info))

        except Exception as e:
            errors.append(f"Error in {sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
