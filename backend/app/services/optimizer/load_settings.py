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
