import httpx
from typing import List, Tuple, Dict

BASE_URL = "https://api.the-odds-api.com/v4"
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

# THE FILTERS
MIN_EV = 1.5
MIN_WIN_PROB = 0.35
MAX_EV_CAP = 15.0

# THE SPORTS
SPORTS = ["basketball_nba", "baseball_mlb"]

# THE BATCHES (Reduced to keep the API from choking)
MARKET_BATCHES = [
    ["spreads", "totals"],
    ["player_points", "player_rebounds", "player_assists"],
    ["player_threes", "pitcher_strikeouts", "batter_home_runs"]
]

MARKET_LABELS = {
    "spreads": "Spread", "totals": "Total", "player_points": "Points",
    "player_rebounds": "Rebounds", "player_assists": "Assists",
    "player_threes": "3PT Made", "pitcher_strikeouts": "Strikeouts",
    "batter_home_runs": "Home Runs"
}

# ── MATH UTILS ───────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    return f"+{round((d - 1) * 100)}" if d >= 2 else str(round(-100 / (d - 1)))

def implied_prob(o: float) -> float:
    return 1 / american_to_decimal(o)

def no_vig_prob(p1: float, p2: float) -> Tuple[float, float]:
    pa, pb = implied_prob(p1), implied_prob(p2)
    return pa / (pa + pb), pb / (pa + pb)

def _fmt_side(name: str, pt: float, m_key: str, desc: str = "") -> str:
    prefix = f"{desc} " if desc else ""
    if m_key == "totals": return f"{name} {abs(pt)}"
    if any(x in m_key for x in ["player", "pitcher", "batter"]): return f"{prefix}{name} {pt}"
    return f"{name} {pt:+}"

# ── THE ENGINE ───────────────────────────────────────────────────────────────

def find_ev_bets(api_key: str):
    all_bets = []
    errors = []
    
    # Clean the key one last time
    api_key = api_key.strip()

    for sport in SPORTS:
        for batch in MARKET_BATCHES:
            try:
                params = {
                    "apiKey": api_key,
                    "regions": "us",
                    "markets": ",".join(batch),
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
                    "oddsFormat": "american"
                }
                
                with httpx.Client(timeout=15) as client:
                    r = client.get(f"{BASE_URL}/sports/{sport}/odds", params=params)
                    
                    if r.status_code == 401:
                        errors.append(f"Auth Failed: Check if key '{api_key[:5]}...' is correct.")
                        return [], errors # Stop early if the key is rejected
                    
                    if r.status_code == 429:
                        errors.append("Usage Quota Hit! (Real 429 error)")
                        return all_bets, errors
                        
                    r.raise_for_status()
                    events = r.json()

                for event in events:
                    # Find Pinnacle and Novig bookmakers
                    bms = {bm["key"]: bm for bm in event.get("bookmakers", [])}
                    pin, nov = bms.get(SHARP_BOOK), bms.get(TARGET_BOOK)
                    if not pin or not nov: continue

                    for pin_mkt in pin["markets"]:
                        m_key = pin_mkt["key"]
                        nov_mkt = next((m for m in nov["markets"] if m["key"] == m_key), None)
                        if not nov_mkt: continue

                        for p_out in pin_mkt["outcomes"]:
                            # Find matching Novig outcome
                            n_out = next((o for o in nov_mkt["outcomes"] 
                                         if o["name"] == p_out["name"] 
                                         and o.get("point") == p_out.get("point")
                                         and o.get("description") == p_out.get("description")), None)
                            if not n_out: continue
                            
                            # Find the opposite side to devig Pinnacle
                            opp_p = next((o for o in pin_mkt["outcomes"] 
                                         if o["name"] != p_out["name"] 
                                         and o.get("point") == p_out.get("point")
                                         and o.get("description") == p_out.get("description")), None)
                            if not opp_p: continue

                            fair_p, _ = no_vig_prob(p_out["price"], opp_p["price"])
                            ev = (fair_p * american_to_decimal(n_out["price"]) - 1) * 100

                            if MIN_EV < ev < MAX_EV_CAP and fair_p >= MIN_WIN_PROB:
                                all_bets.append({
                                    "Sport": sport.split("_")[1].upper(),
                                    "Game": f"{event['away_team']} @ {event['home_team']}",
                                    "Market": MARKET_LABELS.get(m_key, m_key),
                                    "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key, n_out.get("description", "")),
                                    "Novig Odds": f"+{int(n_out['price'])}" if n_out['price'] > 0 else str(int(n_out['price'])),
                                    "Fair Odds": decimal_to_american(1/fair_p),
                                    "EV %": round(ev, 2)
                                })
            except Exception as e:
                errors.append(f"Engine Error ({sport}): {str(e)}")

    return sorted(all_bets, key=lambda x: x["EV %"], reverse=True), errors
