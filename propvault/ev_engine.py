import httpx
from datetime import datetime, timezone
from typing import Optional

BASE_URL = "https://api.the-odds-api.com/v4"
MIN_EV = 1.5
MAX_EV_CAP = 10.0      # Filters out "stale" or "error" lines
MIN_WIN_PROB = 0.35    # Kills +871 garbage; focuses on -110 to +185
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = ["basketball_nba", "baseball_mlb"]
MAIN_MARKETS = ["spreads", "totals"]
# Common props for NBA and MLB
PROP_MARKETS = ["player_points", "player_rebounds", "player_assists", "player_threes", "player_home_runs"]

MARKET_LABELS = {
    "spreads": "Spread",
    "totals": "Total",
    "player_points": "Points",
    "player_rebounds": "Rebounds",
    "player_assists": "Assists",
    "player_threes": "3PT Made",
    "player_home_runs": "Home Runs"
}

# ── Math ──────────────────────────────────────────────────────────────────────

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

# ── API Logic ─────────────────────────────────────────────────────────────────

def fetch_bulk_odds(api_key: str, sport: str, markets: str) -> list[dict]:
    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {"apiKey": api_key, "regions": "us", "markets": markets, "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

def fetch_event_props(api_key: str, sport: str, event_id: str) -> list[dict]:
    url = f"{BASE_URL}/sports/{sport}/events/{event_id}/odds"
    params = {"apiKey": api_key, "regions": "us", "markets": ",".join(PROP_MARKETS), "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}", "oddsFormat": "american"}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        return resp.json().get("bookmakers", [])

# ── Processing ────────────────────────────────────────────────────────────────

def _fmt_side(name: str, point: float, market_key: str, description: str = "") -> str:
    if "player_" in market_key:
        return f"{description} {name} {point}"
    if market_key == "totals":
        return f"{name} {abs(point)}"
    pt = f"+{point}" if point > 0 else str(point)
    return f"{name} {pt}"

def find_ev_bets(api_key: str) -> tuple[list[dict], list[str]]:
    all_bets = []
    errors = []

    for sport in SPORTS:
        try:
            # 1. Process Main Markets (Spreads/Totals)
            bulk_events = fetch_bulk_odds(api_key, sport, ",".join(MAIN_MARKETS))
            
            for event in bulk_events:
                game_name = f"{event['away_team']} vs {event['home_team']}"
                pinnacle = next((b for b in event["bookmakers"] if b["key"] == SHARP_BOOK), None)
                novig = next((b for b in event["bookmakers"] if b["key"] == TARGET_BOOK), None)

                if not pinnacle or not novig: continue

                for pin_mkt in pinnacle["markets"]:
                    m_key = pin_mkt["key"]
                    nov_mkt = next((m for m in novig["markets"] if m["key"] == m_key), None)
                    if not nov_mkt: continue

                    # Match by outcome name and point
                    for p_out in pin_mkt["outcomes"]:
                        n_out = next((o for o in nov_mkt["outcomes"] if o["name"] == p_out["name"] and o.get("point") == p_out.get("point")), None)
                        if not n_out: continue
                        
                        # Find the "Other" side for devigging
                        other_p = next((o for o in pin_mkt["outcomes"] if o["name"] != p_out["name"] and o.get("point") == p_out.get("point")), None)
                        if not other_p: continue

                        fair_prob, _ = no_vig_prob(p_out["price"], other_p["price"])
                        ev = calc_ev(fair_prob, american_to_decimal(n_out["price"]))

                        if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                            all_bets.append({
                                "Sport": sport.split("_")[1].upper(), "Game": game_name, "Market": MARKET_LABELS.get(m_key, m_key),
                                "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key),
                                "Novig Odds": fmt_odds(int(n_out["price"])), "Fair Odds": decimal_to_american(1/fair_prob), "EV %": round(ev, 2)
                            })

            # 2. Process Player Props
            for event in bulk_events[:8]: # Limit to next 8 games to save API quota
                prop_bms = fetch_event_props(api_key, sport, event["id"])
                p_pin = next((b for b in prop_bms if b["key"] == SHARP_BOOK), None)
                p_nov = next((b for b in prop_bms if b["key"] == TARGET_BOOK), None)
                
                if not p_pin or not p_nov: continue

                for pin_mkt in p_pin["markets"]:
                    m_key = pin_mkt["key"]
                    nov_mkt = next((m for m in p_nov["markets"] if m["key"] == m_key), None)
                    if not nov_mkt: continue

                    for p_out in pin_mkt["outcomes"]:
                        # Find matching player and line on Novig
                        n_out = next((o for o in nov_mkt["outcomes"] if o["description"] == p_out["description"] and o["name"] == p_out["name"] and o.get("point") == p_out.get("point")), None)
                        if not n_out: continue

                        other_p = next((o for o in pin_mkt["outcomes"] if o["description"] == p_out["description"] and o["name"] != p_out["name"] and o.get("point") == p_out.get("point")), None)
                        if not other_p: continue

                        fair_prob, _ = no_vig_prob(p_out["price"], other_p["price"])
                        ev = calc_ev(fair_prob, american_to_decimal(n_out["price"]))

                        if MIN_EV < ev < MAX_EV_CAP and fair_prob >= MIN_WIN_PROB:
                            all_bets.append({
                                "Sport": sport.split("_")[1].upper(), "Game": f"{event['away_team']} vs {event['home_team']}",
                                "Market": MARKET_LABELS.get(m_key, m_key), "Side": _fmt_side(n_out["name"], n_out.get("point", 0), m_key, n_out["description"]),
                                "Novig Odds": fmt_odds(int(n_out["price"])), "Fair Odds": decimal_to_american(1/fair_prob), "EV %": round(ev, 2)
                            })
        except Exception as e:
            errors.append(f"Error fetching {sport}: {str(e)}")

    all_bets.sort(key=lambda x: x["EV %"], reverse=True)
    return all_bets, errors
