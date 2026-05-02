# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/core/security.py
# Author:  Bas Arens
# Purpose: JWT signing/verification and the FastAPI dependency that protects
#          authenticated routes. Tokens are HS256-signed with JWT_SECRET and
#          carry the user's email in the `sub` claim plus a standard `exp`.
#
# Functions:
#   create_access_token  — sign a JWT for a given email
#   decode_token         — verify signature + expiry, return payload
#   get_current_user     — FastAPI dependency; 401s on missing/bad token
# ─────────────────────────────────────────────────────────────────────────────

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.services.users import find_user_by_email

JWT_ALGORITHM = "HS256"

# auto_error=False so we can return a consistent 401 instead of FastAPI's 403
# when the Authorization header is missing.
_bearer = HTTPBearer(auto_error=False)


def create_access_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Niet geautoriseerd",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None or creds.scheme.lower() != "bearer":
        raise unauth
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise unauth

    email = payload.get("sub")
    if not email:
        raise unauth

    user = find_user_by_email(email)
    if user is None:
        # Token was valid but the user was deleted — reject.
        raise unauth

    # Strip the password hash before handing the user object to route handlers.
    return {k: v for k, v in user.items() if k != "password_hash"}
