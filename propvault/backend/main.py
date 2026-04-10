"""
PropVault +EV Engine — Backend
Fetches Pinnacle (sharp) and Novig lines from The Odds API,
strips vig from Pinnacle to get fair probabilities,
compares against Novig to find +EV opportunities.
"""

import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

app = FastAPI(title="PropVault +EV Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"
MIN_EV = 1.5  # minimum EV% to surface a bet

SHARP_BOOK = "pinnacle"
TARGET_BOOK = "novig"

SPORTS = [
    "baseball_mlb",
    "basketball_nba",
]

MARKETS = ["h2h", "spreads", "totals"]


# ── Math helpers ──────────────────────────────────────────────────────────────

def american_to_decimal(american: float) -> float:
    if american > 0:
        return american / 100 + 1
    return 100 / abs(american) + 1


def decimal_to_american(decimal: float) -> str:
    if decimal >= 2:
        return f"+{round((decimal - 1) * 100)}"
    return str(round(-100 / (decimal - 1)))


def implied_prob(american: float) -> float:
    return 1 / american_to_decimal(american)


def no_vig_prob(price_a: float, price_b: float) -> tuple[float, float]:
    """Additive devig: strip vig from a two-sided market."""
    pa = implied_prob(price_a)
    pb = implied_prob(price_b)
    total = pa + pb
    return pa / total, pb / total


def calc_ev(fair_prob: float, novig_decimal: float) -> float:
    """EV as a percentage."""
    return (fair_prob * novig_decimal - 1) * 100


# ── Odds API helpers ──────────────────────────────────────────────────────────

async def fetch_odds(sport: str, markets: str) -> list[dict]:
    """Fetch odds from The Odds API for a sport and market set."""
    url = f"{BASE_URL}/sports/{sport}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": markets,
        "bookmakers": f"{SHARP_BOOK},{TARGET_BOOK}",
        "oddsFormat": "american",
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def extract_book_lines(event: dict, book_key: str) -> Optional[dict]:
    """Pull a specific bookmaker's lines from an event."""
    for bm in event.get("bookmakers", []):
        if bm["key"] == book_key:
            return bm
    return None


def get_outcomes_map(market: dict) -> dict[str, float]:
    """Map outcome name → american odds for a market."""
    return {o["name"]: o["price"] for o in market.get("outcomes", [])}


def get_market(bookmaker: dict, market_key: str) -> Optional[dict]:
    for m in bookmaker.get("markets", []):
        if m["key"] == market_key:
            return m
    return None


def format_sport(sport_key: str) -> str:
    mapping = {
        "baseball_mlb": "MLB",
        "basketball_nba": "NBA",
        "americanfootball_nfl": "NFL",
        "icehockey_nhl": "NHL",
    }
    return mapping.get(sport_key, sport_key.upper())


def format_market(market_key: str) -> str:
    mapping = {"h2h": "Moneyline", "spreads": "Spread", "totals": "Total"}
    return mapping.get(market_key, market_key)


# ── Core EV logic ─────────────────────────────────────────────────────────────

def find_ev_bets(events: list[dict], sport_key: str, market_key: str) -> list[dict]:
    results = []

    for event in events:
        game = f"{event['away_team']} vs {event['home_team']}"
        commence = event.get("commence_time", "")

        pinnacle = extract_book_lines(event, SHARP_BOOK)
        novig = extract_book_lines(event, TARGET_BOOK)

        if not pinnacle or not novig:
            continue

        pin_market = get_market(pinnacle, market_key)
        nov_market = get_market(novig, market_key)

        if not pin_market or not nov_market:
            continue

        pin_outcomes = get_outcomes_map(pin_market)
        nov_outcomes = get_outcomes_map(nov_market)

        # Need exactly 2 sides for additive devig
        if len(pin_outcomes) != 2:
            continue

        sides = list(pin_outcomes.keys())
        price_a = pin_outcomes[sides[0]]
        price_b = pin_outcomes[sides[1]]

        fair_a, fair_b = no_vig_prob(price_a, price_b)
        fair_map = {sides[0]: fair_a, sides[1]: fair_b}

        for side_name, fair_prob in fair_map.items():
            if side_name not in nov_outcomes:
                continue

            nov_price = nov_outcomes[side_name]
            nov_decimal = american_to_decimal(nov_price)
            ev = calc_ev(fair_prob, nov_decimal)

            if ev < MIN_EV:
                continue

            fair_decimal = 1 / fair_prob
            fair_american = decimal_to_american(fair_decimal)

            results.append({
                "id": f"{event['id']}_{market_key}_{side_name}",
                "sport": format_sport(sport_key),
                "game": game,
                "market": format_market(market_key),
                "side": side_name,
                "novig_odds": nov_price,
                "fair_odds": fair_american,
                "fair_prob": round(fair_prob * 100, 2),
                "ev": round(ev, 2),
                "commence_time": commence,
            })

    return results


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ev-bets")
async def get_ev_bets():
    if not ODDS_API_KEY:
        raise HTTPException(status_code=500, detail="ODDS_API_KEY not set in environment")

    all_bets = []

    for sport in SPORTS:
        for market in MARKETS:
            try:
                events = await fetch_odds(sport, market)
                bets = find_ev_bets(events, sport, market)
                all_bets.extend(bets)
            except httpx.HTTPStatusError as e:
                # Log and continue — don't crash if one sport/market fails
                print(f"Error fetching {sport}/{market}: {e}")
                continue

    # Sort by EV descending
    all_bets.sort(key=lambda b: b["ev"], reverse=True)

    avg_ev = round(sum(b["ev"] for b in all_bets) / len(all_bets), 2) if all_bets else 0

    return {
        "bets": all_bets,
        "count": len(all_bets),
        "avg_ev": avg_ev,
        "top_ev": all_bets[0]["ev"] if all_bets else 0,
        "min_ev_threshold": MIN_EV,
    }
