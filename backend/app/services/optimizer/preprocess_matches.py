from app.services.sportlink import infer_field_size, infer_duration

def preprocess_matches(matches, settings):
    fields = settings["fields"]
    windows = settings["windows"]
    lockers = settings["lockers"]

    # Map team → window
    window_map = {w["team"]: w for w in windows}

    enriched = []

    for m in matches:
        home = m["thuisteam"]
        away = m["uitteam"]

        team_name = home  # scheduling based on home team mainly

        enriched.append({
            "code": m["wedstrijdcode"],
            "home": home,
            "away": away,
            "date": m["wedstrijddatum"].split("T")[0],
            "duration": infer_duration(team_name),
            "field_size": infer_field_size(team_name),

            # Team time window (default fallback)
            "start_pref": window_map.get(team_name, {}).get("start", "09:00"),
            "end_pref":   window_map.get(team_name, {}).get("end", "17:00"),

            # Field configuration
            "fields": fields,
            "lockers": lockers,
        })

    return enriched
