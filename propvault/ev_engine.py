import httpx
import time
import requests
from datetime import datetime
from typing import Optional

BASE_URL = "https://parlay-api.com/v1"
MIN_EV = 2.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40      
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba", "baseball_mlb"]
MAIN_MARKETS = ["spreads", "totals"]
PROP_MARKETS = ["player_points", "player_rebounds", "player_assists", "player_threes", "pitcher_strikeouts", "batter_home_runs"]

MARKET_LABELS = {
    "spreads": "Spread", "totals": "Total", "player_points": "Points",
    "player_rebounds": "Rebounds", "player_assists": "Assists",
    "player_threes": "3PT Made", "pitcher_strikeouts": "Strikeouts",
    "batter_home_runs": "Home Runs"
}

# ── Math ──────────────────────────────────────────────────────────────────────
def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    return f"+{round((d - 1) * 100)}" if d >= 2 else str(round(-100 / (d - 1)))

def no_vig_prob(price_a: float, price_b: float) -> tuple[float, float]:
    pa, pb = 1/american_to_decimal(price_a), 1/american_to_decimal(price_b)
    total = pa + pb
    return pa / total, pb / total

def fmt_odds(o: int) -> str:
    return f"+{o}" if o > 0 else str(o)

# ── Processing ────────────────────────────────────────────────────────────────
def _fmt_side(name: str, point: float, market_key: str, description: str = "") -> str:
    if any(x in market_key for x in ["player_", "pitcher_", "batter_"]):
        prefix = f"{description} " if description else ""
        return f"{prefix}{name} {point}"
    if market_key == "totals": return f"{name} {abs(point)}"
    pt = f"+{point}" if point > 0 else str(point)
    return f"{name} {pt}"

# ── API Logic ─────────────────────────────────────────────────────────────────
def find_ev_bets(api_key):
    all_bets = []
    errors = []
    target_markets = "h2h,spreads,totals,player_points,player_assists,pitcher_strikeouts"
    
    for sport in ["basketball_nba", "baseball_mlb"]:
        # Use the EXACT URL from their website example
        url = f"https://parlay-api.com/v1/sports/{sport}/odds"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": target_markets,
            "oddsFormat": "american"
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                continue

            events = response.json()
            for event in events:
                # FIX: Use 'title' and lowercase it to match your SHARP_BOOK variable
                bookies = {b['title'].lower(): b['markets'] for b in event.get('bookmakers', [])}
                
                # Check for "pinnacle" and "novig" in the titles
                if "pinnacle" in bookies and "novig" in bookies:
                    for s_mkt in bookies["pinnacle"]:
                        m_key = s_mkt['key']
                        n_mkt = next((m for m in bookies["novig"] if m['key'] == m_key), None)
                        
                        if n_mkt and len(s_mkt['outcomes']) == 2:
                            s_outs = s_mkt['outcomes']
                            try:
                                p1_fair, p2_fair = no_vig_prob(s_outs[0]['price'], s_outs[1]['price'])
                            except: continue

                            for i in range(2):
                                # Outcome matching
                                n_out = next((o for o in n_mkt['outcomes'] if o['name'] == s_outs[i]['name'] and o.get('point') == s_outs[i].get('point')), None)
                                
                                if n_out:
                                    fair_prob = p1_fair if i == 0 else p2_fair
                                    ev = (fair_prob * american_to_decimal(n_out["price"]) - 1) * 100
                                    
                                    if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                        all_bets.append({
                                            "Game": f"{event['away_team']} @ {event['home_team']}",
                                            "Market": MARKET_LABELS.get(m_key, m_key.replace('_', ' ').title()),
                                            "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key, n_out.get("description", "")),
                                            "Novig Odds": fmt_odds(int(n_out["price"])),
                                            "Fair Odds": decimal_to_american(1/fair_prob),
                                            "EV %": round(ev, 2)
                                        })
        except Exception as e:
            errors.append(f"Error on {sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets[:30], errors
