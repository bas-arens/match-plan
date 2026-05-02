# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/optimization.py
# Author:  Bas Arens
# Purpose: Optimization endpoints that load settings, fetch Sportlink matches,
#          and dispatch to the selected solver (Greedy, SA, or CP-SAT).
#
# Endpoints:
#   GET  /optimize/settings      — return all saved settings (fields, lockers, etc.)
#   POST /optimize/run           — run the optimizer for a given date and return
#                                  the resulting schedule
#   POST /optimize/score         — stateless: score a given schedule (used by
#                                  the Gantt to live-update after drag-and-drop)
#   POST /optimize/score-current — score the existing Sportlink schedule for a
#                                  date so the user sees the baseline penalty
# ─────────────────────────────────────────────────────────────────────────────

import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.optimizer.load_settings import load_all_settings
from app.services.sportlink import get_matches_for_date, infer_duration, infer_field_size

from app.services.optimizer.greedy_solver import GreedyScheduler
from app.services.optimizer.sa_solver import SAScheduler
from app.services.optimizer.cpsat_solver import CPSATScheduler
from app.services.optimizer.scoring import score_schedule

router = APIRouter(
    prefix="/optimize",
    tags=["Optimization"],
    dependencies=[Depends(get_current_user)],
)


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
            solver = CPSATScheduler(matches, fields, lockers, preferences, fixed_slots=fixed_slots, priorities=priorities, time_limit=60)
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
    score = score_schedule(result, preferences=preferences, priorities=priorities, lockers=lockers)

    return {
        "status": "ok",
        "algorithm": algo,
        "date": date,
        "elapsed_ms": elapsed_ms,
        "total_penalty": score["total"],
        "penalty_items": score["items"],
        "scheduled": result,
    }


# -----------------------
# POST /optimize/score
# -----------------------
class ScoreRequest(BaseModel):
    scheduled: list[dict]


@router.post("/score")
async def score(req: ScoreRequest):
    """
    Stateless scorer: given a schedule, return its penalty breakdown using
    the canonical scoring function. Used by the Gantt chart to re-score live
    after drag-and-drop, so the frontend never has its own scoring logic.
    """
    s = load_all_settings()
    out = score_schedule(
        req.scheduled,
        preferences=s["preferences"],
        priorities=s.get("priorities", {"lockers": 1, "time_windows": 1, "field_preference": 1, "home_away_layout": 1}),
        lockers=s["lockers"],
    )
    return {"total": out["total"], "items": out["items"]}


# -----------------------
# POST /optimize/score-current
# -----------------------
class ScoreCurrentRequest(BaseModel):
    date: str


def _norm(s):
    # collapse internal whitespace too — "Veld  1" and "Veld 1" both → "veld 1"
    return " ".join((s or "").split()).casefold()


# Sportlink sub-field suffix → (field_size, lane index in the Gantt's 4-lane
# layout). Lanes are A1, A2, B1, B2 (indices 0-3). "A" / "B" cover two lanes.
_SUBFIELD_LAYOUT = {
    "a1": (0.25, 0),
    "a2": (0.25, 1),
    "b1": (0.25, 2),
    "b2": (0.25, 3),
    "a":  (0.5,  0),
    "b":  (0.5,  2),
}


def _match_locker_id(raw, locker_by_name):
    """
    Sportlink locker formats vary: "2", "5R", "1L", "9 - Thuisteam",
    "Kleedkamer 1", or "" (empty). Resolve by:
      1. take the part before " - " (drops "Thuisteam"/"Uitteam" descriptors)
      2. strip a leading "Kleedkamer " prefix
      3. exact (case-insensitive) match against lockers.json → returns its id
      4. otherwise fall back to the cleaned string itself so two matches
         with the same Sportlink locker still trigger sharing detection
         (e.g. both "1L" → both return "1L"); empty/missing → None
    """
    if not raw:
        return None
    s = " ".join(raw.split()).strip()
    if not s:
        return None
    primary = s.split(" - ", 1)[0].strip()
    if primary.lower().startswith("kleedkamer "):
        primary = primary[len("kleedkamer "):].strip()
    if not primary:
        return None
    hit = locker_by_name.get(primary.casefold())
    if hit is not None:
        return hit
    return primary


def _resolve_veld(veld_raw, fields_by_name_full):
    """
    Sportlink writes the veld as "Veld 1", "veld 1 A1", "veld 2 B" etc. The
    trailing "A1" / "B" is a sub-field denoting which part of the full field
    is being used. Returns (field_id, field_name, sub) where sub is the lower-
    cased suffix or None, and field_name is taken from fields.json so the
    Gantt row label is consistent.

    Match by exact name first, then by prefix on a word boundary so "Veld 1"
    matches "veld 1 A1" but not "veld 12".
    """
    v = _norm(veld_raw)
    if not v:
        return None
    # exact match: no sub-field
    hit = fields_by_name_full.get(v)
    if hit:
        return (hit["id"], hit["name"], None)
    # prefix match: capture the suffix
    for name_norm, f in fields_by_name_full.items():
        prefix = name_norm + " "
        if v.startswith(prefix):
            sub = v[len(prefix):].strip() or None
            return (f["id"], f["name"], sub)
    return None


def _build_current_schedule(matches, fields, lockers):
    # Sportlink returns the field/locker as a name string; map to our ids.
    # Matches without a kickoff time or a recognizable field are treated as
    # "unscheduled" and excluded from scoring.
    fields_by_name_full = {_norm(f.get("name")): f for f in fields}
    locker_by_name      = {_norm(l.get("name")): l["id"] for l in lockers}

    schedule = []
    unscheduled = 0
    for i, m in enumerate(matches):
        time_raw = m.get("aanvangstijd")
        veld_raw = m.get("veld")
        if not time_raw or not veld_raw:
            unscheduled += 1
            continue
        resolved = _resolve_veld(veld_raw, fields_by_name_full)
        if resolved is None:
            unscheduled += 1
            continue
        field_id, field_name, sub = resolved

        time_hhmm = time_raw[:5] if len(time_raw) >= 5 else time_raw
        home = m.get("thuisteam") or ""

        # Sportlink's sub-field suffix wins over team-name inference; falls
        # back to inferred size when Sportlink only gives the full-field name.
        layout = _SUBFIELD_LAYOUT.get(sub) if sub else None
        if layout:
            field_size, lane_override = layout
        else:
            field_size, lane_override = infer_field_size(home), None

        entry = {
            "match_id":    str(m.get("wedstrijdcode") or f"AUTO_{i}"),
            "home":        home,
            "away":        m.get("uitteam") or "",
            "time":        time_hhmm,
            "duration":    infer_duration(home),
            "field_id":    field_id,
            "field_name":  field_name,
            "field_size":  field_size,
            "home_locker": _match_locker_id(m.get("kleedkamerthuisteam"), locker_by_name),
            "away_locker": _match_locker_id(m.get("kleedkameruitteam"), locker_by_name),
        }
        if lane_override is not None:
            entry["laneOverride"] = lane_override
        schedule.append(entry)
    return schedule, unscheduled


@router.post("/score-current")
async def score_current(req: ScoreCurrentRequest):
    """
    Scores the current Sportlink schedule for the given date using the same
    canonical scoring as the optimizer. Lets the user see the baseline penalty
    they'd get without running the optimizer.
    """
    date = req.date
    settings = load_all_settings()
    fields      = settings["fields"]
    lockers     = settings["lockers"]
    preferences = settings["preferences"]
    fixed_slots = settings.get("fixed_slots", [])
    priorities  = settings.get("priorities", {"lockers": 1, "time_windows": 1, "field_preference": 1})

    matches = await get_matches_for_date(date)
    if not matches:
        return {"status": "empty", "total_penalty": 0, "optimum_estimate": 0, "penalty_items": [], "unscheduled": 0, "scored": 0}

    schedule, unscheduled = _build_current_schedule(matches, fields, lockers)

    if not schedule:
        return {
            "status": "unscheduled",
            "algorithm": "sportlink",
            "total_penalty": 0,
            "optimum_estimate": None,
            "penalty_items": [],
            "scheduled": [],
            "unscheduled": unscheduled,
            "scored": 0,
        }

    # score_schedule mutates each entry to set its `penalty` field, so the
    # returned `scheduled` list is ready for MatchPlanPage / GanttChart to
    # render (same shape as the optimizer's /run output).
    score = score_schedule(schedule, preferences=preferences, priorities=priorities, lockers=lockers)

    # Greedy baseline: gives the frontend a relative reference for "how good
    # is the current Sportlink schedule?" without committing to a full solver
    # run. Greedy is fast (~tens of ms) so this is fine to do inline. If it
    # fails for any reason we just return None and the UI degrades gracefully.
    optimum_estimate = None
    try:
        greedy = GreedyScheduler(matches, fields, lockers, preferences,
                                 fixed_slots=fixed_slots, priorities=priorities)
        greedy_result = greedy.solve()
        optimum_estimate = score_schedule(
            greedy_result, preferences=preferences, priorities=priorities, lockers=lockers,
        )["total"]
    except Exception as e:
        print(f"score-current: greedy baseline failed: {e}")

    return {
        "status": "ok",
        "algorithm": "sportlink",
        "date": date,
        "total_penalty": score["total"],
        "optimum_estimate": optimum_estimate,
        "penalty_items": score["items"],
        "scheduled": schedule,
        "unscheduled": unscheduled,
        "scored": len(schedule),
    }
