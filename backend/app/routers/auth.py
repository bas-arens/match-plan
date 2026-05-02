# ─────────────────────────────────────────────────────────────────────────────
# File:    backend/app/routers/auth.py
# Author:  Bas Arens
# Purpose: Authentication endpoints. Issues HS256-signed JWTs from the
#          email/password pair stored in app/data/users.json and exposes
#          a whoami endpoint for the frontend to validate its session.
#
# Endpoints:
#   POST /auth/login  — { email, password } → { token, user }
#   GET  /auth/me     — protected; returns the user behind the bearer token
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token, get_current_user
from app.services.users import find_user_by_email, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    email: str
    name: str | None = None


class LoginResponse(BaseModel):
    token: str
    user: UserOut


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = find_user_by_email(body.email)
    # Same error for "no such user" and "wrong password" so we don't leak which.
    if user is None or not verify_password(body.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verkeerd e-mailadres of wachtwoord.",
        )
    token = create_access_token(user["email"])
    return LoginResponse(token=token, user=UserOut(email=user["email"], name=user.get("name")))


@router.get("/me", response_model=UserOut)
def me(current=Depends(get_current_user)):
    return UserOut(email=current["email"], name=current.get("name"))
