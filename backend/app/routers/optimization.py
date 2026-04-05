# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/optimization.py
# Author:  Bas Arens
# Purpose: Optimization endpoints that load settings, fetch Sportlink matches,
#          and dispatch to the selected solver (Greedy, SA, or MILP).
#
# Endpoints:
#   GET  /optimize/settings — return all saved settings (fields, lockers, etc.)
#   POST /optimize/run      — run the optimizer for a given date and return
#                             the resulting schedule
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.optimizer.load_settings import load_all_settings
from app.services.sportlink import get_matches_for_date

from app.services.optimizer.greedy_solver import GreedyScheduler
from app.services.optimizer.milp_solver import MILPScheduler
from app.services.optimizer.sa_solver import SAScheduler

router = APIRouter(prefix="/optimize", tags=["Optimization"])


# Registry of available solvers
ALGORITHMS = {
    "greedy": GreedyScheduler,
    "milp":   MILPScheduler,
    "sa":     SAScheduler,
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

    
    date = req.date
        
    # Load all config files
    settings = load_all_settings()

    fields      = settings["fields"]
    lockers     = settings["lockers"]
    preferences = settings["preferences"]
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

    if algo == "greedy":
        solver = GreedyScheduler(matches, fields, lockers, preferences)
        result = solver.solve()

    elif algo == "sa":
        solver = SAScheduler(matches, fields, lockers, preferences)
        result = solver.solve()

    elif algo == "milp":
        solver = MILPScheduler(matches, fields, lockers, preferences, date)
        solver.build()
        result = solver.solve()

    else:
        raise HTTPException(400, f"Unknown algorithm '{algo}'")

    return {
        "status": "ok",
        "algorithm": algo,
        "date": date,
        "scheduled": result
    }
