"""
PropVault — EV Engine
All math and Odds API fetching lives here.
"""

import httpx
from datetime import datetime, timezone
from typing import Optional

BASE_URL = "https://api.the-odds-api.com/v4"
MIN_EV = 1.5
SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"
SPORTS = ["baseball_mlb", "basketball_nba"]
MARKETS = ["h2h", "spreads", "totals"]

SPORT_LABELS = {
    "baseball_mlb": "MLB",
    "basketball_nba": "NBA",
}
MARKET_LABELS = {
    "h2h": "Moneyline",
    "spreads": "Spread",
    "totals": "Total",
}


# ── Math ──────────────────────────────────────────────────────────────────────

def american_to_decimal(o: float) -> float:
    return o / 100 + 1 if o > 0 else 100 / abs(o) + 1


def decimal_to_american(d: float) -> str:
    return f"+{round((d - 1) * 100)}" if d >= 2 else str(round(-100 / (d - 1)))


def implied_prob(o: float) -> float:
    return 1 / american_to_decimal(o)


def no_vig_prob(price_a: float, price_b: float) -> tuple[float, float]:
    """Additive devig on a two-sided market. Returns (fair_a, fair_b)."""
    pa, pb = implied_prob(price_a), implied_prob(price_b)
    total = pa + pb
    return pa / total, pb / total


def calc_ev(fair_prob: float, novig_decimal: float) -> float:
    """EV as a percentage."""
    return (fair_prob * novig_decimal - 1) * 100


def fmt_odds(o: int) -> str:
    return f"+{o}" if o > 0 else str(o)


# ── Odds API ──────────────────────────────────────────────────────────────────

def fetch_odds(api_key: str, sport: str, market: str) -> list[dict]:
    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": market,
        "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
        "oddsFormat": "american",
    }
    with httpx.Client(timeout=10) as client:
        resp = client.get(url, params=params)
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


def _outcomes_map(market: dict) -> dict[str, float]:
    return {o["name"]: o["price"] for o in market.get("outcomes", [])}


def _outcomes_point_map(market: dict) -> dict[str, tuple[float, float]]:
    """For spreads/totals: map outcome name → (price, point) so we can match on point value."""
    result = {}
    for o in market.get("outcomes", []):
        result[o["name"]] = (o["price"], o.get("point", 0))
    return result


def _lines_match(pin_map: dict, nov_map: dict, market_key: str) -> bool:
    """
    For spreads and totals, both books must post the same point values.
    If they differ, the lines aren't comparable and we skip.
    """
    if market_key not in ("spreads", "totals"):
        return True
    pin_points = {name: pt for name, (_, pt) in pin_map.items()}
    nov_points = {name: pt for name, (_, pt) in nov_map.items()}
    return pin_points == nov_points


# ── Core pipeline ─────────────────────────────────────────────────────────────

def _fmt_side(name: str, point: float, market_key: str) -> str:
    """Append point value for spreads and totals."""
    if market_key not in ("spreads", "totals") or point == 0:
        return name
    pt = f"+{point}" if point > 0 else str(point)
    if market_key == "totals":
        return f"Over {abs(point)}" if name == "Over" else f"Under {abs(point)}"
    return f"{name} {pt}"

def find_ev_bets(api_key: str) -> tuple[list[dict], list[str]]:
    """
    Returns (bets, errors).
    bets  — list of +EV opportunities sorted by EV descending
    errors — any non-fatal fetch errors encountered
    """
    all_bets: list[dict] = []
    errors: list[str] = []

    for sport in SPORTS:
        for market in MARKETS:
            try:
                events = fetch_odds(api_key, sport, market)
            except httpx.HTTPStatusError as e:
                errors.append(f"{sport}/{market}: HTTP {e.response.status_code}")
                continue
            except Exception as e:
                errors.append(f"{sport}/{market}: {e}")
                continue

            for event in events:
                # Skip games that have already started (live lines are unreliable)
                commence = event.get("commence_time", "")
                try:
                    game_time = datetime.fromisoformat(commence.replace("Z", "+00:00"))
                    if game_time < datetime.now(timezone.utc):
                        continue
                except Exception:
                    pass

                game = f"{event['away_team']} vs {event['home_team']}"
                pinnacle = _get_book(event, SHARP_BOOK)
                novig    = _get_book(event, TARGET_BOOK)
                if not pinnacle or not novig:
                    continue

                pin_mkt = _get_market(pinnacle, market)
                nov_mkt = _get_market(novig, market)
                if not pin_mkt or not nov_mkt:
                    continue

                pin_map = _outcomes_point_map(pin_mkt)
                nov_map = _outcomes_point_map(nov_mkt)

                # Skip if fewer than 2 Pinnacle sides or books post different lines
                if len(pin_map) != 2:
                    continue
                if not _lines_match(pin_map, nov_map, market):
                    continue

                sides = list(pin_map.keys())
                pin_price_a = pin_map[sides[0]][0]
                pin_price_b = pin_map[sides[1]][0]
                fair_a, fair_b = no_vig_prob(pin_price_a, pin_price_b)
                fair_map = {sides[0]: fair_a, sides[1]: fair_b}

                for side, fair_prob in fair_map.items():
                    if side not in nov_map:
                        continue
                    nov_price   = nov_map[side][0]
                    nov_decimal = american_to_decimal(nov_price)
                    ev          = calc_ev(fair_prob, nov_decimal)

                    # Sanity cap — real +EV bets don't exceed 15%
                    if ev < MIN_EV or ev > 15:
                        continue

                    all_bets.append({
                        "Sport":      SPORT_LABELS.get(sport, sport.upper()),
                        "Game":       game,
                        "Market":     MARKET_LABELS.get(market, market),
                        "Side":       _fmt_side(side, nov_map[side][1], market),
                        "Novig Odds": fmt_odds(int(nov_price)),
                        "Fair Odds":  decimal_to_american(1 / fair_prob),
                        "Fair Prob":  f"{fair_prob * 100:.1f}%",
                        "EV %":       round(ev, 2),
                    })

    all_bets.sort(key=lambda b: b["EV %"], reverse=True)
    return all_bets, errors
