# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/optimizer/load_settings.py
# Author:  Bas Arens
# Purpose: Thin loaders that read each settings JSON file from app/data/ and
#          return plain Python dicts/lists for the optimizer solvers.
#
# Functions:
#   load_fields()       — read fields.json
#   load_lockers()      — read lockers.json
#   load_preferences()  — read preferences.json
#   load_optimizer()    — read optimizer.json
#   load_all_settings() — convenience wrapper returning all four as one dict
# ─────────────────────────────────────────────────────────────────────────────

import json
from pathlib import Path

SETTINGS_DIR = Path("app/data")

def load_fields():
    return json.loads((SETTINGS_DIR / "fields.json").read_text())

def load_lockers():
    return json.loads((SETTINGS_DIR / "lockers.json").read_text())

def load_preferences():
    return json.loads((SETTINGS_DIR / "preferences.json").read_text())

def load_optimizer():
    return json.loads((SETTINGS_DIR / "optimizer.json").read_text())

def load_all_settings():
    """Convenience function to load all saved settings"""
    return {
        "fields": load_fields(),
        "lockers": load_lockers(),
        "preferences": load_preferences(),
        "optimizer": load_optimizer(),
    }
