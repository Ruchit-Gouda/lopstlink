"""Account routes: signup, login, token refresh and profile."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    SignupRequest,
)
from app.services.auth import (
    AuthError,
    build_profile,
    create_account,
    is_valid_email,
    normalize_email,
    refresh_session,
    session_payload,
    sign_in,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _raise(error: AuthError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest):
    email = normalize_email(payload.email)
    full_name = payload.full_name.strip()

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")

    if len(full_name) < 2:
        raise HTTPException(status_code=400, detail="Enter your full name.")

    if len(payload.password.strip()) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long.",
        )

    try:
        create_account(email=email, password=payload.password, full_name=full_name)
        session = sign_in(email=email, password=payload.password)
    except AuthError as error:
        _raise(error)

    user = session.get("user") or {}

    return {
        "session": session_payload(session),
        "user": build_profile(user),
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = normalize_email(payload.email)

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")

    try:
        session = sign_in(email=email, password=payload.password)
    except AuthError as error:
        _raise(error)

    user = session.get("user") or {}

    return {
        "session": session_payload(session),
        "user": build_profile(user),
    }


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest):
    try:
        session = refresh_session(payload.refresh_token)
    except AuthError as error:
        _raise(error)

    user = session.get("user") or {}

    return {
        "session": session_payload(session),
        "user": build_profile(user),
    }


@router.get("/me", response_model=MeResponse)
def me(user: dict = Depends(get_current_user)):
    return {"user": build_profile(user)}
