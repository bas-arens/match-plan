# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/core/config.py
# Author:  Bas Arens
# Purpose: Application configuration loaded from the .env file.
#          Provides a global `settings` singleton used throughout the backend
#          for the Sportlink client ID and dynamically set club details.
#
# Fields:
#   SPORTLINK_CLIENT_ID  — API key for the Sportlink data platform (required)
#   CLUB_NAME            — populated at startup from Sportlink /clubgegevens
#   CLUB_CODE            — populated at startup from Sportlink /clubgegevens
# ─────────────────────────────────────────────────────────────────────────────

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SPORTLINK_CLIENT_ID: str
    
    CLUB_NAME: str | None = None
    CLUB_CODE: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()


