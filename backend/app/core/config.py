# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/core/config.py
# Author:  Bas Arens
# Purpose: Application configuration loaded from the .env file.
#          Provides a global `settings` singleton used throughout the backend
#          for the Sportlink client ID, JWT auth, and dynamically set club details.
#
# Fields:
#   SPORTLINK_CLIENT_ID   — API key for the Sportlink data platform (required)
#   JWT_SECRET            — HS256 signing key for access tokens (required)
#   JWT_EXPIRE_MINUTES    — access-token lifetime in minutes (default 1440 = 24h)
#   CLUB_NAME             — populated at startup from Sportlink /clubgegevens
#   CLUB_CODE             — populated at startup from Sportlink /clubgegevens
# ─────────────────────────────────────────────────────────────────────────────

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPORTLINK_CLIENT_ID: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 1440

    CLUB_NAME: str | None = None
    CLUB_CODE: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()


