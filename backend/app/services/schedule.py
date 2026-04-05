# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/schedule.py
# Author:  Bas Arens
# Purpose: Schedule retrieval service (stub). Returns an empty match list until
#          the planner output is persisted and wired up to this service.
#
# Functions:
#   get_schedule_for_date(date_str) — return stored schedule for a given date
# ─────────────────────────────────────────────────────────────────────────────

def get_schedule_for_date(date_str: str):
    # TODO: koppelen aan jouw planner
    return {
        "date": date_str,
        "matches": []
    }
