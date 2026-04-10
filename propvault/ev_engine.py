import httpx
import time
from typing import List, Tuple, Dict

BASE_URL = "https://api.the-odds-api.com/v4"
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

# THE FILTERS
MIN_EV = 1.5
MIN_WIN_PROB = 0.35
MAX_EV_CAP = 15.0

# SPORT-SPECIFIC MARKET SETS
NBA_BATCHES = [
    ["spreads", "totals"],
    ["player_points", "player_rebounds", "player_assists", "player_threes"]
]

MLB_BATCHES = [
    ["spreads", "totals"],
    ["pitcher_strikeouts", "batter_home_runs"]
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

def no_vig_prob(p1: float, p2: float) -> Tuple[float, float]:
    pa, pb = 1/american_to_decimal(p1), 1/american_to_decimal(p2)
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
    SPORTS = ["basketball_nba", "baseball_mlb"]

    for sport in SPORTS:
        # Step 1: Filter batches by sport to prevent 422 "Unprocessable" errors
        batches = NBA_BATCHES if "basketball" in sport else MLB_BATCHES
        
        for batch in batches:
            try:
                time.sleep(0.2) # Avoid aggressive rate limiting
                params = {
                    "apiKey": api_key,
                    "regions": "us",
                    "markets": ",".join(batch),
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
                    "oddsFormat": "american"
                }
                
                with httpx.Client(timeout=15) as client:
                    r = client.get(f"{BASE_URL}/sports/{sport}/odds", params=params)
                    
                    # Log but skip if the specific book hasn't posted the lines yet
                    if r.status_code == 422:
                        continue
                    
                    r.raise_for_status()
                    events = r.json()

                for event in events:
                    bms = {bm["key"]: bm for bm in event.get("bookmakers", [])}
                    pin, nov = bms.get(SHARP_BOOK), bms.get(TARGET_BOOK)
                    if not pin or not nov: continue

                    for pin_mkt in pin["markets"]:
                        m_key = pin_mkt["key"]
                        nov_mkt = next((m for m in nov["markets"] if m["key"] == m_key), None)
                        if not nov_mkt: continue

                        for p_out in pin_mkt["outcomes"]:
                            n_out = next((o for o in nov_mkt["outcomes"] 
                                         if o["name"] == p_out["name"] 
                                         and o.get("point") == p_out.get("point")
                                         and o.get("description") == p_out.get("description")), None)
                            if not n_out: continue
                            
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
                errors.append(f"Scan for {batch[0]} pending...")

    return sorted(all_bets, key=lambda x: x["EV %"], reverse=True), errors
