# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/models/club.py
# Author:  Bas Arens
# Purpose: Pydantic model representing basic club identity returned by
#          the Sportlink /clubgegevens endpoint.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel

class ClubInfo(BaseModel):
    clubnaam: str
    clubcode: str
