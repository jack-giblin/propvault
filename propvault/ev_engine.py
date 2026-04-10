import httpx
import requests
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "https://parlay-api.com/v1"
MIN_EV = 2.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40      
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "draftkings"

# Markets to request from the API
TARGET_MARKETS = "h2h,spreads,totals,player_points,player_rebounds,player_assists,player_strikeouts"

MARKET_LABELS = {
    "spreads": "Spread", "totals": "Total", "h2h": "Moneyline",
    "player_points": "Points", "player_rebounds": "Rebounds", 
    "player_assists": "Assists", "player_threes": "3PT Made", 
    "pitcher_strikeouts": "Strikeouts", "batter_home_runs": "Home Runs"
}

# ── Math Utilities ────────────────────────────────────────────────────────────
def american_to_decimal(o: float) -> float:
    try:
        if o > 0:
            return (o / 100) + 1
        return (100 / abs(o)) + 1
    except ZeroDivisionError:
        return 1.0

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    if d >= 2.0:
        return f"+{round((d - 1) * 100)}"
    return str(round(-100 / (d - 1)))

def no_vig_prob(price_a: float, price_b: float) -> Tuple[float, float]:
    """Calculates fair probability using the power method or additive method."""
    try:
        da, db = american_to_decimal(price_a), american_to_decimal(price_b)
        pa, pb = 1/da, 1/db
        total = pa + pb
        return pa / total, pb / total
    except Exception:
        return 0.5, 0.5

def fmt_odds(o: int) -> str:
    return f"+{o}" if o > 0 else str(o)

# ── String Formatting ──────────────────────────────────────────────────────────
def _fmt_side(name: str, point: float, market_key: str, description: str = "") -> str:
    # Clean up names (e.g., "Over 220.5" instead of "Over 220.5")
    clean_name = name.strip()
    if any(x in market_key for x in ["player_", "pitcher_", "batter_"]):
        prefix = f"{description} " if description else ""
        return f"{prefix}{clean_name} {point}"
    
    if market_key == "totals": 
        return f"{clean_name} {abs(point)}"
    
    pt_str = f"+{point}" if point > 0 else str(point)
    return f"{clean_name} {pt_str}" if point != 0 else clean_name

# ── API Logic ─────────────────────────────────────────────────────────────────
def find_ev_bets(api_key: str) -> Tuple[List[Dict], List[str]]:
    all_bets = []
    errors = []
    
    # Normalize book names once
    sharp_target = SHARP_BOOK.lower().strip()
    retail_target = TARGET_BOOK.lower().strip()

    for sport in ["basketball_nba", "baseball_mlb"]: 
        url = f"{BASE_URL}/sports/{sport}/odds"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": TARGET_MARKETS,
            "oddsFormat": "american"
        }
        
        try:
            response = requests.get(url, params=params, timeout=12)
            if response.status_code != 200:
                errors.append(f"API Error {response.status_code} on {sport}")
                continue
            
            events = response.json()
            if not events:
                continue

            for event in events:
                # Map bookmakers by lowercased title for easier lookups
                bookies = {b['title'].lower().strip(): b['markets'] for b in event.get('bookmakers', [])}
                
                if sharp_target in bookies and retail_target in bookies:
                    for s_mkt in bookies[sharp_target]:
                        m_key = s_mkt['key']
                        
                        # Find matching market in DraftKings
                        n_mkt = next((m for m in bookies[retail_target] if m['key'] == m_key), None)
                        
                        # We only analyze 2-way markets (Over/Under, Spread/Spread, Team A/Team B)
                        if n_mkt and len(s_mkt['outcomes']) == 2 and len(n_mkt['outcomes']) == 2:
                            s_outs = s_mkt['outcomes']
                            n_outs = n_mkt['outcomes']
                            
                            # 1. Get Fair Probabilities from Sharp (Pinnacle)
                            p1_fair, p2_fair = no_vig_prob(s_outs[0]['price'], s_outs[1]['price'])
                            fairs = [p1_fair, p2_fair]

                            for i in range(2):
                                sharp_side = s_outs[i]
                                fair_prob = fairs[i]
                                
                                # 2. Find matching side in Target Book
                                # Logic: Must match Name AND Point value exactly
                                target_side = next((o for o in n_outs if o['name'] == sharp_side['name'] 
                                                   and float(o.get('point', 0)) == float(sharp_side.get('point', 0))), None)
                                
                                if target_side:
                                    # 3. Calculate EV
                                    # EV = (Fair Prob * Decimal Odds) - 1
                                    target_decimal = american_to_decimal(target_side["price"])
                                    ev = (fair_prob * target_decimal - 1) * 100
                                    
                                    # 4. Filter and Append
                                    if MIN_EV <= ev <= MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                        all_bets.append({
                                            "Game": f"{event['away_team']} @ {event['home_team']}",
                                            "Market": MARKET_LABELS.get(m_key, m_key.replace('_', ' ').title()),
                                            "Side": _fmt_side(target_side["name"], target_side.get("point", 0), m_key, target_side.get("description", "")),
                                            "Target Odds": fmt_odds(int(target_side["price"])),
                                            "Fair Odds": decimal_to_american(1/fair_prob),
                                            "EV %": round(ev, 2)
                                        })
                                        
        except Exception as e:
            errors.append(f"System Error on {sport}: {str(e)}")

    # Sort results by the highest EV
    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
