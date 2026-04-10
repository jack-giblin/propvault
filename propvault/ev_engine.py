import requests
from typing import List, Dict, Tuple

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL = "https://parlay-api.com/v1"
MIN_EV = 2.5
MAX_EV_CAP = 15.0
MIN_WIN_PROB = 0.40      
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "draftkings"
TARGET_MARKETS = "h2h,spreads,totals,player_points,player_rebounds,player_assists,player_strikeouts"

MARKET_LABELS = {
    "spreads": "Spread", "totals": "Total", "h2h": "Moneyline",
    "player_points": "Points", "player_rebounds": "Rebounds", 
    "player_assists": "Assists", "pitcher_strikeouts": "Strikeouts",
    "player_threes": "3PT Made", "batter_home_runs": "Home Runs"
}

# ── Math Utilities ────────────────────────────────────────────────────────────
def american_to_decimal(o: float) -> float:
    return (o / 100) + 1 if o > 0 else (100 / abs(o)) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    return f"+{round((d - 1) * 100)}" if d >= 2.0 else str(round(-100 / (d - 1)))

def no_vig_prob(price_a: float, price_b: float) -> Tuple[float, float]:
    try:
        da, db = american_to_decimal(price_a), american_to_decimal(price_b)
        pa, pb = 1/da, 1/db
        total = pa + pb
        return pa / total, pb / total
    except:
        return 0.5, 0.5

# ── Processing ────────────────────────────────────────────────────────────────
def _fmt_side(name: str, point: float, market_key: str, desc: str = "") -> str:
    clean_name = name.strip()
    p_str = f" {point}" if point != 0 else ""
    if any(x in market_key for x in ["player", "pitcher", "batter"]):
        prefix = f"{desc} " if desc else ""
        return f"{prefix}{clean_name}{p_str}".strip()
    return f"{clean_name}{p_str}".strip()

def find_ev_bets(api_key: str) -> Tuple[List[Dict], List[str]]:
    all_bets, errors = [], []
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
            res = requests.get(url, params=params, timeout=12)
            if res.status_code != 200:
                continue
            
            events = res.json()
            for event in events:
                bookies = {b['title'].lower().strip(): b['markets'] for b in event.get('bookmakers', [])}
                
                if sharp_target in bookies and retail_target in bookies:
                    for s_mkt in bookies[sharp_target]:
                        m_key = s_mkt['key']
                        n_mkt = next((m for m in bookies[retail_target] if m['key'] == m_key), None)
                        
                        if n_mkt and len(s_mkt['outcomes']) == 2 and len(n_mkt['outcomes']) == 2:
                            p1_f, p2_f = no_vig_prob(s_mkt['outcomes'][0]['price'], s_mkt['outcomes'][1]['price'])
                            
                            for i, fair_prob in enumerate([p1_f, p2_f]):
                                s_out = s_mkt['outcomes'][i]
                                n_out = next((o for o in n_mkt['outcomes'] if o['name'] == s_out['name'] 
                                             and float(o.get('point', 0)) == float(s_out.get('point', 0))), None)
                                
                                if n_out:
                                    target_odds = n_out["price"]
                                    ev = (fair_prob * american_to_decimal(target_odds) - 1) * 100
                                    
                                    if MIN_EV <= ev <= MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                        all_bets.append({
                                            "Game": f"{event['away_team']} @ {event['home_team']}",
                                            "Market": MARKET_LABELS.get(m_key, m_key.replace('_', ' ').title()),
                                            "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key, n_out.get("description", "")),
                                            "Target Odds": f"+{int(target_odds)}" if target_odds > 0 else str(int(target_odds)),
                                            "Fair Odds": decimal_to_american(1/fair_prob),
                                            "EV %": round(ev, 2)
                                        })
        except Exception as e:
            errors.append(f"{sport} error: {str(e)}")
    
    return sorted(all_bets, key=lambda x: x["EV %"], reverse=True), errors
