# app/services/sportlink.py

import httpx
from datetime import datetime, timedelta
from app.core.config import settings
import logging


BASE_URL = "https://data.sportlink.com"


# -----------------------------------------------------------
# 🔧 Algemene fetch helper
# -----------------------------------------------------------
async def fetch(endpoint: str, params: dict = None):
    if params is None:
        params = {}

    params["client_id"] = settings.SPORTLINK_CLIENT_ID

    url = f"{BASE_URL}/{endpoint}"

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)

        if response.status_code == 404:
            raise ValueError(f"Endpoint niet gevonden: {url}")

        response.raise_for_status()
        return response.json()


# -----------------------------------------------------------
# 📌 1. CLUBGEGEVENS
# Sportlink artikel: "Clubgegevens"
# -----------------------------------------------------------
async def get_club_info():
    data = await fetch("clubgegevens")

    gegevens = data.get("gegevens")
    if not gegevens:
        raise ValueError("Sportlink retourneert geen clubgegevens.")

    return {
        "club_name": gegevens.get("clubnaam"),
        "club_code": gegevens.get("clubcode"),
        "raw": gegevens
    }

# -----------------------------------------------------------
# 📌 Clublogo — direct afbeelding vanuit Sportlink
# -----------------------------------------------------------
async def get_club_logo():
    """
    Geeft de URL terug naar het clublogo via Sportlink endpoint /clublogo.
    Dit endpoint retourneert een afbeelding, geen JSON.
    Daarom geven wij alleen de URL terug.
    """
    client_id = settings.SPORTLINK_CLIENT_ID
    return f"{BASE_URL}/clublogo?client_id={client_id}"


# -----------------------------------------------------------
# 📌 2. PROGRAMMA — Alle wedstrijden van de club
# Sportlink artikel: "Programma"
# -----------------------------------------------------------
async def get_all_matches():
    """
    Haalt ALLE wedstrijden op die Sportlink beschikbaar houdt voor de club.
    (ongefilterd)
    """
    return await fetch("programma")


# -----------------------------------------------------------
# 📌 Helper: bepaal of match thuiswedstrijd is
# -----------------------------------------------------------
def is_home_match(match, club_code: str):
    home_code = (match.get("thuisteamclubrelatiecode") or "").upper()
    return home_code == club_code


# -----------------------------------------------------------
# 📌 3. Lijst van thuiswedstrijddatums
# -----------------------------------------------------------
async def get_home_match_dates():
    raw = await get_all_matches()
    dates = set()

    for m in raw:
        dt = m.get("wedstrijddatum")
        if not dt:
            continue

        date_only = dt.split("T")[0]

        # Alleen thuiswedstrijden
        if not is_home_match(m, settings.CLUB_CODE):
            continue

        real_date = datetime.strptime(date_only, "%Y-%m-%d")
        dates.add(real_date.strftime("%Y-%m-%d"))

    return sorted(dates)



# -----------------------------------------------------------
# 📌 4. Wedstrijden per datum
# -----------------------------------------------------------
async def get_matches_for_date(date_str: str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d")

    raw = await get_all_matches()
    result = []

    for m in raw:
        dt = m.get("wedstrijddatum")
        if not dt:
            continue

        api_date = datetime.strptime(dt.split("T")[0], "%Y-%m-%d")

        if api_date != target_date:
            continue

        if not is_home_match(m, settings.CLUB_CODE):
            continue

        result.append(m)

    return result


# -----------------------------------------------------------
# 📌 5. Wedstrijd-informatie voor 1 wedstrijd
# Sportlink artikel: "Wedstrijd-informatie"
# -----------------------------------------------------------
async def get_match_info(wedstrijdcode: str):
    params = {"wedstrijdcode": wedstrijdcode}
    data = await fetch("wedstrijd-informatie", params=params)

    info = data.get("wedstrijdinformatie")
    if not info:
        raise ValueError(f"Geen wedstrijd-informatie voor code {wedstrijdcode}")

    return info



# -----------------------------------------------------------
# 📌 6. Wedstrijd-statistieken voor 1 wedstrijd
async def get_match_statistics(wedstrijdcode: str):
    url = (
        f"{BASE_URL}/wedstrijd-statistieken"
        f"?client_id={settings.SPORTLINK_CLIENT_ID}"
        f"&wedstrijdcode={wedstrijdcode}"
    )

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()

        data = response.json()
        # Sportlink geeft data terug onder de key "wedstrijdstatistieken"
        return data.get("wedstrijdstatistieken", data)


# -----------------------------------------------------------
async def get_teams():
    data = await fetch("teams")

    # Case 1 — Sportlink returns {"teams": [...]}
    if isinstance(data, dict):
        teams = data.get("teams")
    # Case 2 — Sportlink returns a raw list [...]
    elif isinstance(data, list):
        teams = data
    else:
        raise ValueError("Onbekend Sportlink formaat voor /teams.")

    if not teams:
        raise ValueError("Geen teams gevonden in Sportlink response.")

    categories = {}

    for t in teams:
        teamnaam = t.get("teamnaam")
        category = t.get("leeftijdscategorie")

        # ❌ Skip entries without leeftijdscategorie
        if not category or category.strip() == "":
            continue

        # ❌ Skip missing team names
        if not teamnaam:
            continue

        # Ensure category bucket exists
        if category not in categories:
            categories[category] = []

        # Avoid duplicates inside each category
        if teamnaam not in categories[category]:
            categories[category].append(teamnaam)

    return categories


async def enrich_match_info(match: dict, client_id: str):
    """
    Enrich Sportlink match with:
    - duration (minutes) from /wedstrijd-informatie
    - field_size inferred from team name
    """

    wedstrijdcode = match.get("wedstrijdcode")

    if not wedstrijdcode:
        match["duration"] = None
        match["field_size"] = infer_field_size(match["thuisteam"])
        return match

    url = f"{BASE_URL}/wedstrijd-informatie?client_id={client_id}&wedstrijdcode={wedstrijdcode}"

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        data = resp.json()
        info = data.get("wedstrijdinformatie", {}) or {}

        # --- Duration ---
        duur = info.get("duur")
        if duur:
            try:
                match["duration"] = int(float(duur))
            except:
                match["duration"] = None
        else:
            match["duration"] = None

        # --- Field size (ALWAYS infer from team name) ---
        match["field_size"] = infer_field_size(match["thuisteam"])

    except Exception as e:
        logging.warning(f"Enrichment failed for {wedstrijdcode}: {e}")
        match["duration"] = None
        match["field_size"] = infer_field_size(match["thuisteam"])

    return match



# -----------------------------------------------------------
# 🔎 Extra: veldgrootte & speelduur afleiden (zoals in jouw vorige project)
# -----------------------------------------------------------

def infer_field_size(team_name: str) -> float:
    t = team_name.upper()

    if any(x in t for x in ("JO7","JO8","JO9","MO7","MO8","MO9","JO10","MO10")):
        return 0.25
    if any(x in t for x in ("JO11","MO11", "JO12","MO12")):
        return 0.5
    return 1.0


def infer_duration(team_name: str) -> int:
    t = team_name.upper()

    if any(x in t for x in ("JO7","MO7")):
        return 55
    if any(x in t for x in ("JO8","MO8","JO9","MO9")):
        return 65
    if any(x in t for x in ("JO10","MO10","JO11","MO11")):
        return 75
    if any(x in t for x in ("JO12","MO12","JO13","MO13")):
        return 75
    if any(x in t for x in ("JO14","MO14","JO15","MO15")):
        return 85
    if any(x in t for x in ("JO16","MO16","JO17","MO17")):
        return 95
    return 105


