import httpx
import time
from datetime import datetime
from typing import Optional

BASE_URL = "https://api.the-odds-api.com/v4"
MIN_EV = 1.5
MAX_EV_CAP = 15.0  # Increased slightly to catch those high-value unicorns
MIN_WIN_PROB = 0.35      
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

# ── API Logic ─────────────────────────────────────────────────────────────────
def fetch_bulk_odds(api_key: str, sport: str, markets: str) -> list[dict]:
    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {"apiKey": api_key, "regions": "us", "markets": markets, "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

def fetch_event_props(api_key: str, sport: str, event_id: str) -> list[dict]:
    # Added a tiny sleep here to prevent 422/429 errors during the loop
    time.sleep(0.3) 
    url = f"{BASE_URL}/sports/{sport}/events/{event_id}/odds"
    params = {"apiKey": api_key, "regions": "us", "markets": ",".join(PROP_MARKETS), "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        if resp.status_code != 200: return []
        return resp.json().get("bookmakers", [])

# ── Processing ────────────────────────────────────────────────────────────────
def _fmt_side(name: str, point: float, market_key: str, description: str = "") -> str:
    if any(x in market_key for x in ["player_", "pitcher_", "batter_"]):
        prefix = f"{description} " if description else ""
        return f"{prefix}{name} {point}"
    if market_key == "totals": return f"{name} {abs(point)}"
    pt = f"+{point}" if point > 0 else str(point)
    return f"{name} {pt}"

def find_ev_bets(api_key: str) -> tuple[list[dict], list[str]]:
    all_bets = []
    errors = []
    api_key = api_key.strip()

    for sport in SPORTS:
        try:
            bulk_events = fetch_bulk_odds(api_key, sport, ",".join(MAIN_MARKETS))
            
            for event in bulk_events:
                # 1. Check Main Markets (Spreads/Totals)
                pinnacle = next((b for b in event["bookmakers"] if b["key"] == SHARP_BOOK), None)
                novig = next((b for b in event["bookmakers"] if b["key"] == TARGET_BOOK), None)

                if pinnacle and novig:
                    for pin_mkt in pinnacle["markets"]:
                        nov_mkt = next((m for m in novig["markets"] if m["key"] == pin_mkt["key"]), None)
                        if not nov_mkt: continue

                        for p_out in pin_mkt["outcomes"]:
                            n_out = next((o for o in nov_mkt["outcomes"] if o["name"] == p_out["name"] and o.get("point") == p_out.get("point")), None)
                            other_p = next((o for o in pin_mkt["outcomes"] if o["name"] != p_out["name"] and o.get("point") == p_out.get("point")), None)
                            
                            if n_out and other_p:
                                fair_prob, _ = no_vig_prob(p_out["price"], other_p["price"])
                                ev = (fair_prob * american_to_decimal(n_out["price"]) - 1) * 100
                                if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                    all_bets.append({
                                        "Sport": sport.split("_")[1].upper(), "Game": f"{event['away_team']} @ {event['home_team']}",
                                        "Market": MARKET_LABELS.get(pin_mkt["key"], pin_mkt["key"]),
                                        "Side": _fmt_side(n_out["name"], n_out.get("point", 0), pin_mkt["key"]),
                                        "Novig Odds": fmt_odds(int(n_out["price"])), "Fair Odds": decimal_to_american(1/fair_prob), "EV %": round(ev, 2)
                                    })

                # 2. Check Player Props for this specific event
                prop_bms = fetch_event_props(api_key, sport, event["id"])
                p_pin = next((b for b in prop_bms if b["key"] == SHARP_BOOK), None)
                p_nov = next((b for b in prop_bms if b["key"] == TARGET_BOOK), None)
                
                if p_pin and p_nov:
                    for pin_mkt in p_pin["markets"]:
                        nov_mkt = next((m for m in p_nov["markets"] if m["key"] == pin_mkt["key"]), None)
                        if not nov_mkt: continue

                        for p_out in pin_mkt["outcomes"]:
                            n_out = next((o for o in nov_mkt["outcomes"] if o.get("description") == p_out.get("description") and o["name"] == p_out["name"] and o.get("point") == p_out.get("point")), None)
                            other_p = next((o for o in pin_mkt["outcomes"] if o.get("description") == p_out.get("description") and o["name"] != p_out["name"] and o.get("point") == p_out.get("point")), None)
                            
                            if n_out and other_p:
                                fair_prob, _ = no_vig_prob(p_out["price"], other_p["price"])
                                ev = (fair_prob * american_to_decimal(n_out["price"]) - 1) * 100
                                if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                                    all_bets.append({
                                        "Sport": sport.split("_")[1].upper(), "Game": f"{event['away_team']} @ {event['home_team']}",
                                        "Market": MARKET_LABELS.get(pin_mkt["key"], pin_mkt["key"]), 
                                        "Side": _fmt_side(n_out["name"], n_out.get("point", 0), pin_mkt["key"], n_out.get("description", "")),
                                        "Novig Odds": fmt_odds(int(n_out["price"])), "Fair Odds": decimal_to_american(1/fair_prob), "EV %": round(ev, 2)
                                    })

        except Exception as e:
            errors.append(f"Notice: {sport} updates pending. ({str(e)})")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
