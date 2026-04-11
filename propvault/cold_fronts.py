import requests
from datetime import date

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MLB_PLAYER_URL = "https://statsapi.mlb.com/api/v1/people"


def get_today_pitchers():
    r = requests.get(MLB_SCHEDULE_URL, params={
        "sportId": 1,
        "date": date.today().isoformat()
    }, timeout=10)

    data = r.json()
    pitchers = []

    for day in data.get("dates", []):
        for game in day.get("games", []):
            for side in ["home", "away"]:
                p = game.get("teams", {}).get(side, {}).get("probablePitcher")
                if p:
                    pitchers.append({
                        "id": p["id"],
                        "name": p["fullName"]
                    })

    return pitchers


def get_k9(player_id):
    r = requests.get(f"{MLB_PLAYER_URL}/{player_id}/stats", params={
        "stats": "season",
        "group": "pitching",
        "season": 2025
    }, timeout=10)

    splits = r.json().get("stats", [{}])[0].get("splits", [])
    if not splits:
        return None

    s = splits[0]["stat"]

    ip = float(s.get("inningsPitched", 0))
    ks = float(s.get("strikeOuts", 0))

    if ip == 0:
        return None

    return (ks / ip) * 9


def get_recent_k9(player_id):
    r = requests.get(f"{MLB_PLAYER_URL}/{player_id}/stats", params={
        "stats": "gameLog",
        "group": "pitching",
        "season": 2025
    }, timeout=10)

    games = r.json().get("stats", [{}])[0].get("splits", [])[:5]

    ks = 0
    ip = 0

    for g in games:
        s = g.get("stat", {})
        ks += float(s.get("strikeOuts", 0))
        ip += float(s.get("inningsPitched", 0))

    if ip == 0:
        return None

    return (ks / ip) * 9


def get_cold_fronts():
    pitchers = get_today_pitchers()
    results = []

    for p in pitchers:
        k9 = get_k9(p["id"])
        recent_k9 = get_recent_k9(p["id"])

        if k9 is None or recent_k9 is None:
            continue

        delta = recent_k9 - k9

        cold_score = (k9 * -0.3) + (-delta * 1.2)

        results.append({
            "name": p["name"],
            "k9": round(k9, 1),
            "cold_score": round(cold_score, 2)
        })

    return sorted(results, key=lambda x: x["cold_score"], reverse=True)
