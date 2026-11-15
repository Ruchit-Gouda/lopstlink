"""Shared authentication dependencies."""

from typing import Any

from fastapi import Depends, Header, HTTPException

from app.services.auth import AuthError, get_user_from_token


def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Return the Supabase user for the bearer token, or raise 401."""

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user = get_user_from_token(token)
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_user(
    authorization: str | None = Header(default=None),
) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        return get_user_from_token(token)
    except AuthError:
        return None


CurrentUser = Depends(get_current_user)
