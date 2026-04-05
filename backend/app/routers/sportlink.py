# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/sportlink.py
# Author:  Bas Arens
# Purpose: FastAPI router that proxies all Sportlink data to the frontend.
#
# Endpoints:
#   GET /sportlink/clubgegevens          — full club info passthrough
#   GET /sportlink/programma             — all matches (unfiltered)
#   GET /sportlink/logo                  — club logo URL
#   GET /sportlink/programma/datum       — home matches on a specific date
#   GET /sportlink/programma/datumlijst  — list of unique home match dates
#   GET /sportlink/wedstrijd/{code}      — full match info for one match
#   GET /sportlink/wedstrijd/statistieken/{code} — match statistics
#   GET /sportlink/teams                 — teams grouped by age category
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, Query
from app.services import sportlink

router = APIRouter(
    prefix="/sportlink",
    tags=["Sportlink API"]
)

# -----------------------------------------------------------
# 📌 1. Clubgegevens — exact wat Sportlink terugstuurt
# -----------------------------------------------------------
@router.get("/clubgegevens")
async def clubgegevens():
    """
    Haalt **clubgegevens** op via Sportlink.

    Dit bevat o.a.:
    - clubnaam & clubcode  
    - tenues (shirt, broek, sokken)  
    - adresgegevens  
    - contactgegevens  
    - website & social links  
    - logo + klein logo  
    - oprichtingsdatum  
    - bankgegevens  

    ⚠ *Dit is een directe passthrough van het Sportlink /clubgegevens endpoint.*
    """
    try:
        return await sportlink.get_club_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------
# 📌 2. Programma — alle wedstrijden van de club
# -----------------------------------------------------------
@router.get("/programma")
async def programma():
    """
    Haalt het **volledige programma** op van de club via Sportlink.

    Dit programma bevat per wedstrijd o.a.:
    - wedstrijddatum + tijd  
    - wedstrijdcode & wedstrijdnummer  
    - thuisteam + uitteam + logo's  
    - veld, accommodatie, plaats  
    - kleedkamers (indien beschikbaar)  
    - scheidsrechters  
    - competitiegegevens (klasse, poule, soort)

    ⚠ Dit is het Sportlink artikel **'Programma'**, zonder filtering.
    """
    try:
        return await sportlink.get_all_matches()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------
# 📌 Clublogo — directe URL naar het clublogo
# -----------------------------------------------------------
@router.get("/logo")
async def club_logo():
    """
    Geeft enkel de URL terug naar het clublogo via Sportlink.
    Dit wordt gebruikt door de frontend navbar.
    """
    try:
        url = await sportlink.get_club_logo()
        return {"logo": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# -----------------------------------------------------------
# 📌 3. Programma voor een datum — thuiswedstrijden
# -----------------------------------------------------------
@router.get("/programma/datum")
async def programma_op_datum(
    datum: str = Query(..., description="Datum in formaat YYYY-MM-DD")
):
    """
    Geeft **alle thuiswedstrijden op één dag**, gebaseerd op het Sportlink 'Programma'.

    Een wedstrijd bevat o.a.:
    - `wedstrijddatum` (ISO timestamp)
    - `wedstrijdcode`, `wedstrijdnummer`
    - thuisteam / uitteam + logo's
    - aanvangstijd
    - veld & accommodatie
    - kleedkamers:
      - `kleedkamerthuisteam`
      - `kleedkameruitteam`
      - `kleedkamerscheidsrechter`
    - wedstrijdstatus (bijv. “Te spelen”)
    - scheidsrechters met volledige namen
    - competitiegegevens: competitie, poule, klasse

    ⚠ Dit is een filter op:
    - datums
    - thuiswedstrijden van jouw eigen club
    """
    try:
        return await sportlink.get_matches_for_date(datum)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------
# 📌 4. Datumlijst — unieke speeldagen
# -----------------------------------------------------------
@router.get("/programma/datumlijst")
async def datumlijst():
    """
    Geeft een **lijst met unieke datums** waarop de club thuis speelt.

    De lijst bevat strings in `YYYY-MM-DD` formaat.

    Gebaseerd op Sportlink 'Programma' en gefilterd op:
    - thuiswedstrijden  
    - unieke speeldagen  
    """
    try:
        return await sportlink.get_home_match_dates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------
# 📌 5. Wedstrijdinformatie — details van één wedstrijd
# -----------------------------------------------------------
@router.get("/wedstrijd/{wedstrijdcode}")
async def wedstrijd_informatie(wedstrijdcode: str):
    """
    Haalt **volledige informatie van één wedstrijd** op via het Sportlink artikel
    **'Wedstrijd-informatie'**.

    Dit bevat uitgebreide details zoals:
    - veldtype, veldlocatie
    - wedstrijdduur
    - aanvangstijd + datum
    - officials (scheidsrechters + assistenten)
    - thuis- & uitteam details
    - accommodatie (adres, plaats)
    - kleedkamers: thuis, uit, official
    - competitiegegevens (type, klasse, poule)
    - opmerkingen en metadata

    ⚠ Dit is NIET hetzelfde als het Programma-artikel.
      Dit endpoint geeft veel meer informatie terug.
    """
    try:
        return await sportlink.get_match_info(wedstrijdcode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------

@router.get("/wedstrijd/statistieken/{wedstrijdcode}")
async def wedstrijd_statistieken(wedstrijdcode: str):
    """
    Haalt **wedstrijdstatistieken** op via Sportlink.

    Dit bevat o.a.:
    - thuisteam: naam, thuisgewonnen, uitgewonnen,
      percentagegewonnen, percentagethuisgewonnen, percentageuitgewonnen
    - uitteam: dezelfde statistieken als thuisteam

    Gebruikt Sportlink artikel: **Wedstrijd-statistieken**.
    """
    try:
        return await sportlink.get_match_statistics(wedstrijdcode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------

@router.get("/teams")
async def teams():
    """
    Haalt **teams** op via Sportlink.

    Gebruikt Sportlink artikel: **Teams**.
    """
    try:
        return await sportlink.get_teams()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))