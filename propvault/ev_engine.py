import httpx
from datetime import datetime
from typing import Optional

BASE_URL = "https://api.the-odds-api.com/v4"
MIN_EV = 1.5
MAX_EV_CAP = 15.0      
MIN_WIN_PROB = 0.35    
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba", "baseball_mlb"]

# Split these to avoid the 422 error
MARKET_BATCHES = [
    ["spreads", "totals"],
    ["player_points", "player_rebounds", "player_assists", "player_threes", "pitcher_strikeouts", "batter_home_runs"]
]

MARKET_LABELS = {
    "spreads": "Spread",
    "totals": "Total",
    "player_points": "Points",
    "player_rebounds": "Rebounds",
    "player_assists": "Assists",
    "player_threes": "3PT Made",
    "pitcher_strikeouts": "Strikeouts",
    "batter_home_runs": "Home Runs"
}

# ── Math Utilities ────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1: return "+0"
    return f"+{round((d - 1) * 100)}" if d >= 2 else str(round(-100 / (d - 1)))

def implied_prob(o: float) -> float:
    return 1 / american_to_decimal(o)

def no_vig_prob(price_a: float, price_b: float) -> tuple[float, float]:
    pa, pb = implied_prob(price_a), implied_prob(price_b)
    total = pa + pb
    return pa / total, pb / total

def calc_ev(fair_prob: float, novig_decimal: float) -> float:
    return (fair_prob * novig_decimal - 1) * 100

def fmt_odds(o: int) -> str:
    return f"+{o}" if o > 0 else str(o)

def _fmt_side(name: str, point: float, market_key: str, description: str = "") -> str:
    if any(x in market_key for x in ["player_", "pitcher_", "batter_"]):
        prefix = f"{description} " if description else ""
        return f"{prefix}{name} {point}"
    if market_key == "totals":
        return f"{name} {abs(point)}"
    pt = f"+{point}" if point > 0 else str(point)
    return f"{name} {pt}"

# ── API Logic ─────────────────────────────────────────────────────────────────

def find_ev_bets(api_key: str):
    all_bets = []
    errors = []

    for sport in SPORTS:
        # We loop through batches to keep the API happy
        for batch in MARKET_BATCHES:
            try:
                url = f"{BASE_URL}/sports/{sport}/odds"
                params = {
                    "apiKey": api_key, 
                    "regions": "us", 
                    "markets": ",".join(batch), 
                    "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", 
                    "oddsFormat": "american"
                }
                
                with httpx.Client(timeout=20) as client:
                    resp = client.get(url, params=params)
                    
                    # If it still hits a 422, we capture it and move on
                    if resp.status_code == 422:
                        errors.append(f"Batch limit hit for {sport} ({batch[0]}...)")
                        continue
                        
                    resp.raise_for_status()
                    events = resp.json()

                for event in events:
                    game_name = f"{event['away_team']} vs {event['home_team']}"
                    pinnacle = next((b for b in event["bookmakers"] if b["key"] == SHARP_BOOK), None)
                    novig = next((b for b in event["bookmakers"] if b["key"] == TARGET_BOOK), None)

                    if not pinnacle or not novig: continue

                    for pin_mkt in pinnacle["markets"]:
                        m_key = pin_mkt["key"]
                        nov_mkt = next((m for m in novig["markets"] if m["key"] == m_key), None)
                        if not nov_mkt: continue

                        for p_out in pin_mkt["outcomes"]:
                            n_out = next((o for o in nov_mkt["outcomes"] 
                                         if o["name"] == p_out["name"] 
                                         and o.get("point") == p_out.get("point")
                                         and o.get("description") == p_out.get("description")), None)
                            if not n_out: continue
                            
                            other_p = next((o for o in pin_mkt["outcomes"] 
                                           if o["name"] != p_out["name"] 
                                           and o.get("point") == p_out.get("point")
                                           and o.get("description") == p_out.get("description")), None)
                            if not other_p: continue

                            fair_prob, _ = no_vig_prob(p_out["price"], other_p["price"])
                            ev = calc_ev(fair_prob, american_to_decimal(n_out["price"]))

                            if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                all_bets.append({
                                    "Sport": sport.split("_")[1].upper(),
                                    "Game": game_name,
                                    "Market": MARKET_LABELS.get(m_key, m_key),
                                    "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key, n_out.get("description", "")),
                                    "Novig Odds": fmt_odds(int(n_out["price"])),
                                    "Fair Odds": decimal_to_american(1/fair_prob),
                                    "EV %": round(ev, 2)
                                })

            except Exception as e:
                errors.append(f"Error scanning {sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
