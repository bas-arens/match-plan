from pydantic import BaseModel
from typing import List, Optional


# -----------------------
# FIELDS
# -----------------------
class FieldItem(BaseModel):
    id: int
    name: str
    type: str
    surface: str


class FieldsPayload(BaseModel):
    fields: List[FieldItem]


# -----------------------
# LOCKER ROOMS
# -----------------------
class LockerRoom(BaseModel):
    id: int
    name: str


class LockerRoomPayload(BaseModel):
    rooms: List[LockerRoom]


# -----------------------
# TEAM WINDOWS
# -----------------------
class TeamWindowItem(BaseModel):
    team: str
    start: str
    end: str


class TeamWindowPayload(BaseModel):
    windows: List[TeamWindowItem]


# -----------------------
# OPTIMIZER SETTINGS
# -----------------------
class OptimizerSettings(BaseModel):
    algorithm: str
    allow_overlap: bool = False
    priority_teams: Optional[List[str]] = []
