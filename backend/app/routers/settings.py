# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/settings.py
# Author:  Bas Arens
# Purpose: CRUD endpoints for club configuration stored in JSON files under
#          app/data/. Covers fields, locker rooms, team preferences, and
#          optimizer algorithm selection.
#
# Endpoints:
#   GET  /settings/fields       — load saved fields
#   POST /settings/fields       — save fields list
#   GET  /settings/lockers      — load saved locker rooms
#   POST /settings/lockers      — save locker rooms list
#   GET  /settings/preferences  — load team time preferences
#   POST /settings/preferences  — save team time preferences
#   GET  /settings/optimizer    — load optimizer algorithm config
#   POST /settings/optimizer    — save optimizer algorithm config
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os

router = APIRouter(prefix="/settings", tags=["Settings"])

BASE_PATH = "app/data"
os.makedirs(BASE_PATH, exist_ok=True)

# -------------------------
# Generic helpers
# -------------------------
def load_json(name, default):
    path = f"{BASE_PATH}/{name}.json"
    if not os.path.exists(path):
        save_json(name, default)
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(name, data):
    path = f"{BASE_PATH}/{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# -------------------------
# Fields
# -------------------------
class Field(BaseModel):
    id: int
    name: str
    type: str
    surface: str


@router.get("/fields")
def get_fields():
    return load_json("fields", default=[])


@router.post("/fields")
def save_fields(fields: list[Field]):
    save_json("fields", [f.dict() for f in fields])
    return {"status": "saved"}


# -------------------------
# Lockers
# -------------------------
class Locker(BaseModel):
    id: int
    name: str


@router.get("/lockers")
def get_lockers():
    return load_json("lockers", default=[])


@router.post("/lockers")
def save_lockers(lockers: list[Locker]):
    save_json("lockers", [l.dict() for l in lockers])
    return {"status": "saved"}


# -------------------------
# Team Preferences
# -------------------------
class TeamPreference(BaseModel):
    team: str
    start: str
    end: str
    preferred_field_ids: list[int] = []


@router.get("/preferences")
def get_preferences():
    return load_json("preferences", default=[])


@router.post("/preferences")
def save_preferences(preferences: list[TeamPreference]):
    save_json("preferences", [p.dict() for p in preferences])
    return {"status": "saved"}


# -------------------------
# Optimizer
# -------------------------
class OptimizerSettings(BaseModel):
    algorithm: str


@router.get("/optimizer")
def get_optimizer():
    return load_json("optimizer", default={"algorithm": "milp"})


@router.post("/optimizer")
def save_optimizer(opt: OptimizerSettings):
    save_json("optimizer", opt.dict())
    return {"status": "saved"}


# -------------------------
# Fixed Slots
# -------------------------
class FixedSlot(BaseModel):
    team: str
    time: str | None = None
    field_id: int | None = None
    locker_id: int | None = None


@router.get("/fixed-slots")
def get_fixed_slots():
    return load_json("fixed_slots", default=[])


@router.post("/fixed-slots")
def save_fixed_slots(slots: list[FixedSlot]):
    save_json("fixed_slots", [s.dict() for s in slots])
    return {"status": "saved"}
