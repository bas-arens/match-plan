from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.services.sportlink import get_club_info
from app.core.config import settings

# Routers importeren
from app.routers.sportlink import router as sportlink_router
from app.routers.schedule import router as schedule_router
from app.routers.optimization import router as optimization_router

from app.routers.settings import router as settings_router

app = FastAPI(title="MatchPlan API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifespan (vervangt deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⏳ Sportlink clubinfo ophalen...")
    info = await get_club_info()

    if info["club_name"]:
        settings.CLUB_NAME = info["club_name"]
        settings.CLUB_CODE = info["club_code"]
        print(f"✅ Club gevonden: {settings.CLUB_NAME} ({settings.CLUB_CODE})")
    else:
        print("⚠ Geen clubgegevens gevonden, planner werkt beperkt.")

    yield

    print("🔻 Server shutting down...")

app.router.lifespan_context = lifespan

# Routers registreren
app.include_router(sportlink_router)
app.include_router(schedule_router)
app.include_router(optimization_router)

app.include_router(settings_router)


@app.get("/")
async def root():
    return {"status": "running"}
