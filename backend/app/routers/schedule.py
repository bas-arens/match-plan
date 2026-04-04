from fastapi import APIRouter
from app.services.schedule import get_schedule_for_date

router = APIRouter(tags=["Schedule"])

@router.get("/{date_str}")
def schedule(date_str: str):
    return get_schedule_for_date(date_str)
