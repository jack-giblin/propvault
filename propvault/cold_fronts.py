import requests
from datetime import date

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_URL = "https://statsapi.mlb.com/api/v1/people"


# ─────────────────────────────────────────────
# SAFE CONVERSION
# ─────────────────────────────────────────────

def safe_float(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            if " " in x:
                return float(x.split()[0])
            return float(x)
    except:
        return 0.0
    return 0.0


# ─────────────────────────────────────────────
# TODAY'S STARTING PITCHERS (FIXED)
# ─────────────────────────────────────────────

def get_today_pitchers():
    try:
        r = requests.get(
            MLB_SCHEDULE_URL,
            params={
                "sportId": 1,
                "date": date.today().isoformat(),
                "hydrate": "probablePitcher,team"
            },
            timeout=10
        )

        data = r.json()
        pitchers = []

        for day in data.get("dates", []):
            for game in day.get("games", []):

                for side in ["home", "away"]:
                    team = game.get("teams", {}).get(side, {})
                    p = team.get("probablePitcher")

                    if p and p.get("id"):
                        pitchers.append({
                            "id": p["id"],
                            "name": p.get("fullName", "Unknown")
                        })

        return pitchers

    except:
        return []


# ─────────────────────────────────────────────
# SEASON K/9
# ─────────────────────────────────────────────

def get_k9(player_id):
    try:
        r = requests.get(
            f"{MLB_PLAYER_URL}/{player_id}/stats",
            params={
                "stats": "season",
                "group": "pitching",
                "season": 2025
            },
            timeout=10
        )

        splits = r.json().get("stats", [{}])[0].get("splits", [])
        if not splits:
            return 0.0

        s = splits[0]["stat"]

        ip = safe_float(s.get("inningsPitched"))
        ks = safe_float(s.get("strikeOuts"))

        if ip == 0:
            return 0.0

        return (ks / ip) * 9

    except:
        return 0.0


# ─────────────────────────────────────────────
# LAST 5 GAMES K/9
# ─────────────────────────────────────────────

def get_recent_k9(player_id):
    try:
        r = requests.get(
            f"{MLB_PLAYER_URL}/{player_id}/stats",
            params={
                "stats": "gameLog",
                "group": "pitching",
                "season": 2025
            },
            timeout=10
        )

        games = r.json().get("stats", [{}])[0].get("splits", [])[:5]

        ks = 0.0
        ip = 0.0

        for g in games:
            s = g.get("stat", {})
            ks += safe_float(s.get("strikeOuts"))
            ip += safe_float(s.get("inningsPitched"))

        if ip == 0:
            return None

        return (ks / ip) * 9

    except:
        return None


# ─────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────

def get_cold_fronts():
    pitchers = get_today_pitchers()

    if not pitchers:
        return []

    results = []

    for p in pitchers:
        k9 = get_k9(p["id"])
        recent_k9 = get_recent_k9(p["id"])

        # fallback so we NEVER drop players
        if k9 is None:
            k9 = 0.0

        if recent_k9 is None:
            recent_k9 = k9

        delta = recent_k9 - k9

        cold_score = (k9 * -0.25) + (-delta * 1.1)

        results.append({
            "name": p["name"],
            "k9": round(k9, 1),
            "cold_score": round(cold_score, 2)
        })

    return sorted(results, key=lambda x: x["cold_score"], reverse=True)
