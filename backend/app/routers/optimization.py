# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/optimization.py
# Author:  Bas Arens
# Purpose: Optimization endpoints that load settings, fetch Sportlink matches,
#          and dispatch to the selected solver (Greedy, SA, or CP-SAT).
#
# Endpoints:
#   GET  /optimize/settings — return all saved settings (fields, lockers, etc.)
#   POST /optimize/run      — run the optimizer for a given date and return
#                             the resulting schedule
# ─────────────────────────────────────────────────────────────────────────────

import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.optimizer.load_settings import load_all_settings
from app.services.sportlink import get_matches_for_date

from app.services.optimizer.greedy_solver import GreedyScheduler
from app.services.optimizer.sa_solver import SAScheduler
from app.services.optimizer.cpsat_solver import CPSATScheduler
from app.services.optimizer.scoring import score_schedule

router = APIRouter(prefix="/optimize", tags=["Optimization"])


# Registry of available solvers
ALGORITHMS = {
    "greedy": GreedyScheduler,
    "sa":     SAScheduler,
    "cpsat":  CPSATScheduler,
}


# -----------------------
# Request body model
# -----------------------
class OptimizeInput(BaseModel):
    date: str


# -----------------------
# GET /optimize/settings
# -----------------------
@router.get("/settings")
async def get_optimizer_settings():
    """
    Returns saved settings (fields, lockers, windows, optimizer config).
    """
    try:
        # load_all_settings is NOT async → no await
        settings = load_all_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------
# POST /optimize/run
# -----------------------
class RunRequest(BaseModel):
    date: str


@router.post("/run")
async def run_optimizer(req: RunRequest):
    import traceback

    date = req.date

    # Load all config files
    settings = load_all_settings()

    fields      = settings["fields"]
    lockers     = settings["lockers"]
    preferences = settings["preferences"]
    fixed_slots = settings.get("fixed_slots", [])
    priorities  = settings.get("priorities", {"lockers": 1, "time_windows": 1, "field_preference": 1})
    opt_conf    = settings["optimizer"]  # contains: { "algorithm": "greedy" }

    # Fetch matches
    from app.services.sportlink import get_matches_for_date
    matches = await get_matches_for_date(date)

    if not matches:
        return {
            "status": "empty",
            "message": "Geen thuiswedstrijden gevonden."
        }

    algo = opt_conf.get("algorithm", "greedy").lower()

    t0 = time.perf_counter()

    try:
        if algo == "greedy":
            solver = GreedyScheduler(matches, fields, lockers, preferences, fixed_slots=fixed_slots, priorities=priorities)
            result = solver.solve()

        elif algo == "sa":
            solver = SAScheduler(matches, fields, lockers, preferences, fixed_slots=fixed_slots, priorities=priorities)
            result = solver.solve()

        elif algo == "cpsat":
            solver = CPSATScheduler(matches, fields, lockers, preferences, fixed_slots=fixed_slots, priorities=priorities, time_limit=180)
            result = solver.solve()

        else:
            raise HTTPException(400, f"Unknown algorithm '{algo}'")
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Optimizer error:\n{tb}")
        raise HTTPException(500, detail=f"{type(e).__name__}: {e}")

    elapsed_ms = round((time.perf_counter() - t0) * 1000)

    # Canonical scoring: overwrite each entry's penalty field and compute
    # a single total that matches the frontend's calculation.
    score = score_schedule(result, preferences=preferences, priorities=priorities)

    return {
        "status": "ok",
        "algorithm": algo,
        "date": date,
        "elapsed_ms": elapsed_ms,
        "total_penalty": score["total"],
        "penalty_items": score["items"],
        "scheduled": result,
    }
