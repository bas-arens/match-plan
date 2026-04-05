# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/models/match.py
# Author:  Bas Arens
# Purpose: Pydantic model for a single match entry as used internally by the
#          planning system. duration and field_size are inferred at runtime
#          from the team name if not provided by Sportlink.
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel

class Match(BaseModel):
    thuisteam: str
    uitteam: str
    aanvangstijd: str | None = None
    wedstrijddatum: str | None = None
    wedstrijdcode: str | None = None
    duration: int | None = None
    field_size: float | None = None
