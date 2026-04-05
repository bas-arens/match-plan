# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/schedule.py
# Author:  Bas Arens
# Purpose: Schedule retrieval router (stub). Returns an empty match list for a
#          given date until the planner is fully integrated.
#
# Endpoints:
#   GET /{date_str} — retrieve the stored schedule for a date
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter
from app.services.schedule import get_schedule_for_date

router = APIRouter(tags=["Schedule"])

@router.get("/{date_str}")
def schedule(date_str: str):
    return get_schedule_for_date(date_str)
