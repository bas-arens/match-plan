import json
import os
from typing import Dict, Any

SETTINGS_PATH = "app/data/settings.json"


# Ensure file exists
def ensure_settings_file():
    if not os.path.exists("app/data"):
        os.makedirs("app/data")

    if not os.path.isfile(SETTINGS_PATH):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "fields": [],
                "lockerrooms": [],
                "teamwindows": [],
                "optimizer": {
                    "algorithm": "milp",
                    "allow_overlap": False,
                    "priority_teams": []
                }
            }, f, indent=2)


def load_settings() -> Dict[str, Any]:
    ensure_settings_file()
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(data: Dict[str, Any]):
    ensure_settings_file()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
