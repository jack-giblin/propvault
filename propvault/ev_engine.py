"""
PropVault — EV Engine
Uses The Odds API. Makes exactly 2 API calls per refresh (one per sport),
fetching all markets in a single request. Novig is the target book,
Pinnacle is the sharp source.
"""

import requests
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

BASE_URL       = "https://api.the-odds-api.com/v4"
MIN_EV         = 2.0
MAX_EV_CAP     = 15.0
SHARP_BOOK     = "pinnacle"
TARGET_BOOK    = "novig"
SPORTS         = ["baseball_mlb", "basketball_nba"]
MARKETS        = "h2h,spreads,totals"   # single comma-separated string = 1 API call per sport

SPORT_LABELS   = {"baseball_mlb": "MLB", "basketball_nba": "NBA"}
MARKET_LABELS  = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}


# ── Math ──────────────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1

def decimal_to_american(d: float) -> str:
    if d <= 1.001: return "+100"
    return f"+{round((d-1)*100)}" if d >= 2 else str(round(-100 / (d-1)))

def no_vig_prob(price_a: float, price_b: float) -> Tuple[float, float]:
    pa = 1 / american_to_decimal(price_a)
    pb = 1 / american_to_decimal(price_b)
    total = pa + pb
    return pa / total, pb / total

def fmt_odds(o: float) -> str:
    o = int(o)
    return f"+{o}" if o > 0 else str(o)

def fmt_side(name: str, point, market_key: str) -> str:
    if market_key == "totals":
        val = abs(float(point)) if point else 0
        return f"{name} {val:g}"
    if market_key == "spreads":
        val = float(point) if point else 0
        pt = f"+{val:g}" if val > 0 else f"{val:g}"
        return f"{name} {pt}"
    return name


# ── API ───────────────────────────────────────────────────────────────────────

def _fetch_sport(api_key: str, sport: str) -> List[dict]:
    """Single API call — fetches all markets for one sport."""
    resp = requests.get(
        f"{BASE_URL}/sports/{sport}/odds",
        params={
            "apiKey":      api_key,
            "regions":     "us",
            "markets":     MARKETS,
            "bookmakers":  f"{SHARP_BOOK},{TARGET_BOOK}",
            "oddsFormat":  "american",
        },
        timeout=12,
    )
    resp.raise_for_status()
    return resp.json()


def _get_book(event: dict, key: str) -> Optional[dict]:
    for bm in event.get("bookmakers", []):
        if bm["key"] == key:
            return bm
    return None


def _get_market(book: dict, key: str) -> Optional[dict]:
    for m in book.get("markets", []):
        if m["key"] == key:
            return m
    return None


def _outcomes_map(market: dict) -> dict:
    """name → (price, point)"""
    return {
        o["name"]: (o["price"], o.get("point", 0))
        for o in market.get("outcomes", [])
        if o.get("price") is not None
    }


def _points_match(pin_map: dict, nov_map: dict, market_key: str) -> bool:
    """For spreads/totals, both books must post the same point values."""
    if market_key not in ("spreads", "totals"):
        return True
    pin_pts = {n: p for n, (_, p) in pin_map.items()}
    nov_pts = {n: p for n, (_, p) in nov_map.items()}
    return pin_pts == nov_pts


# ── Core pipeline ─────────────────────────────────────────────────────────────

def find_ev_bets(api_key: str) -> Tuple[List[Dict], List[str]]:
    """
    Returns (bets, errors).
    Makes exactly 2 HTTP requests total (one per sport).
    Results are cached by the caller for 5 minutes.
    """
    all_bets: List[Dict] = []
    errors:   List[str]  = []
    now_utc = datetime.now(timezone.utc)

    for sport in SPORTS:
        try:
            events = _fetch_sport(api_key, sport)
        except requests.HTTPError as e:
            errors.append(f"{SPORT_LABELS.get(sport, sport)}: HTTP {e.response.status_code}")
            continue
        except Exception as e:
            errors.append(f"{SPORT_LABELS.get(sport, sport)}: {e}")
            continue

        for event in events:
            # Skip games that have already started
            try:
                ct = datetime.fromisoformat(event["commence_time"].replace("Z", "+00:00"))
                if ct <= now_utc:
                    continue
            except Exception:
                continue

            pinnacle = _get_book(event, SHARP_BOOK)
            novig    = _get_book(event, TARGET_BOOK)
            if not pinnacle or not novig:
                continue

            game  = f"{event['away_team']} @ {event['home_team']}"
            sport_label = SPORT_LABELS.get(sport, sport.upper())

            for market_key in ("h2h", "spreads", "totals"):
                pin_mkt = _get_market(pinnacle, market_key)
                nov_mkt = _get_market(novig, market_key)
                if not pin_mkt or not nov_mkt:
                    continue

                pin_map = _outcomes_map(pin_mkt)
                nov_map = _outcomes_map(nov_mkt)

                if len(pin_map) != 2:
                    continue
                if not _points_match(pin_map, nov_map, market_key):
                    continue

                sides = list(pin_map.keys())
                try:
                    fair_a, fair_b = no_vig_prob(pin_map[sides[0]][0], pin_map[sides[1]][0])
                except Exception:
                    continue

                fair_map = {sides[0]: fair_a, sides[1]: fair_b}

                for side_name, fair_prob in fair_map.items():
                    if side_name not in nov_map:
                        continue

                    nov_price, nov_point = nov_map[side_name]
                    try:
                        ev = (fair_prob * american_to_decimal(nov_price) - 1) * 100
                    except Exception:
                        continue

                    if ev < MIN_EV or ev > MAX_EV_CAP:
                        continue

                    all_bets.append({
                        "Sport":       sport_label,
                        "Game":        game,
                        "Market":      MARKET_LABELS.get(market_key, market_key),
                        "Side":        fmt_side(side_name, nov_point, market_key),
                        "Target Odds": fmt_odds(nov_price),
                        "Fair Odds":   decimal_to_american(1 / fair_prob),
                        "Fair Prob":   f"{fair_prob * 100:.1f}%",
                        "EV %":        round(ev, 2),
                    })

    all_bets.sort(key=lambda b: b["EV %"], reverse=True)
    return all_bets, errors
