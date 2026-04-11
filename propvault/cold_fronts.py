def get_cold_fronts(today_pitchers_stats):
    results = []

    for p in today_pitchers_stats:
        name = p["name"]
        k9 = p["k9"]
        recent_k9 = p["recent_k9"]

        delta = recent_k9 - k9

        cold_score = (k9 * -0.3) + (-delta * 1.2)

        results.append({
            "name": name,
            "k9": round(k9, 1),
            "cold_score": round(cold_score, 2)
        })

    return sorted(results, key=lambda x: x["cold_score"], reverse=True)
