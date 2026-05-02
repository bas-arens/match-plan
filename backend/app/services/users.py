# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/services/users.py
# Author:  Bas Arens
# Purpose: User store backed by app/data/users.json. Read/write helpers and
#          bcrypt password verification used by the auth router and CLI.
#          NOTE: JSON storage is intentionally temporary; will move to the DB
#          alongside the other settings during the JSON→DB migration.
#
# Functions:
#   load_users           — read users.json (returns [] if file missing)
#   save_users           — atomically write users.json
#   find_user_by_email   — case-insensitive lookup
#   verify_password      — bcrypt compare
#   hash_password        — bcrypt hash for new users
# ─────────────────────────────────────────────────────────────────────────────

import json
import os
import tempfile

import bcrypt

USERS_PATH = "app/data/users.json"


def load_users() -> list[dict]:
    if not os.path.exists(USERS_PATH):
        return []
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: list[dict]) -> None:
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    # Atomic write: dump to a temp file in the same dir, then replace.
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(USERS_PATH), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
        os.replace(tmp_path, USERS_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def find_user_by_email(email: str) -> dict | None:
    target = email.strip().lower()
    for user in load_users():
        if user.get("email", "").lower() == target:
            return user
    return None


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plaintext: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False
