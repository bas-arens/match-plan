# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/sportlink_startup.py
# Author:  Bas Arens
# Purpose: Startup helper that fetches club name and code from Sportlink and
#          populates settings.CLUB_NAME / settings.CLUB_CODE so they are
#          available for home-match filtering throughout the application.
#
# Functions:
#   load_club_info() — fetch /clubgegevens and populate global settings
# ─────────────────────────────────────────────────────────────────────────────

import httpx
from app.core.config import settings

SPORTLINK_BASE = "https://data.sportlink.com"

async def load_club_info():
    """
    Haalt clubgegevens op vanuit Sportlink (clubnaam + code)
    en vult automatisch settings.CLUB_NAME & settings.CLUB_CODE.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        url = f"{SPORTLINK_BASE}/clubgegevens?client_id={settings.SPORTLINK_CLIENT_ID}"
        resp = await client.get(url)
        resp.raise_for_status()

        data = resp.json()
        club = data.get("clubgegevens")

        if not club:
            print("⚠ Geen clubgegevens gevonden in Sportlink API.")
            return

        settings.CLUB_NAME = club.get("clubnaam", "").upper().strip()
        settings.CLUB_CODE = club.get("clubcode", "").upper().strip()

        print(f"✔ Sportlink club geladen: {settings.CLUB_NAME} ({settings.CLUB_CODE})")
