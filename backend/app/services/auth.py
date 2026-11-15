"""Supabase Auth helpers.

LostLink uses Supabase Auth as the identity store. Accounts are created and
looked up with the service-role key, which never reaches the browser. Contact
details and Link credits live in the user's metadata so the whole feature works
without extra database migrations.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.config import SUPABASE_SERVICE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

BASE_URL = SUPABASE_URL.rstrip("/")
TIMEOUT = 25.0

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

CONTACT_KEYS = ("contact_name", "contact_email", "contact_phone")


class AuthError(Exception):
    """An authentication problem that maps to a clean API response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def normalize_email(value: str) -> str:
    return value.strip().lower()


def is_valid_email(value: str) -> bool:
    return bool(EMAIL_RE.match(value.strip()))


def _admin_headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }


def _public_headers() -> dict[str, str]:
    return {"apikey": SUPABASE_SERVICE_KEY, "Content-Type": "application/json"}


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _error_detail(response: httpx.Response, fallback: str) -> str:
    data = _json(response)
    for key in ("error_description", "msg", "message", "error"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return fallback


def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    try:
        return httpx.request(method, url, timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as error:
        logger.warning("Supabase Auth request failed: %s", error)
        raise AuthError(
            503,
            "The account service is temporarily unavailable. Please try again.",
        ) from error


def create_account(email: str, password: str, full_name: str) -> dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "full_name": full_name,
            "points": 0,
            "contact_name": full_name,
            "contact_email": email,
            "contact_phone": "",
        },
    }

    response = _request(
        "POST",
        f"{BASE_URL}/auth/v1/admin/users",
        headers=_admin_headers(),
        json=payload,
    )

    if response.status_code >= 400:
        detail = _error_detail(response, "Could not create account.")
        lowered = detail.lower()

        if (
            "already" in lowered
            or "registered" in lowered
            or "exists" in lowered
        ):
            raise AuthError(
                409,
                "An account with this email already exists. Please log in.",
            )

        logger.warning(
            "Supabase signup failed (%s): %s", response.status_code, detail
        )
        raise AuthError(
            400,
            "Could not create your account. Please check your details.",
        )

    return _json(response)


def sign_in(email: str, password: str) -> dict[str, Any]:
    response = _request(
        "POST",
        f"{BASE_URL}/auth/v1/token",
        params={"grant_type": "password"},
        headers=_public_headers(),
        json={"email": email, "password": password},
    )

    if response.status_code == 429:
        raise AuthError(429, "Too many attempts. Please wait a minute.")

    if response.status_code >= 400:
        raise AuthError(401, "Incorrect email or password.")

    return _json(response)


def refresh_session(refresh_token: str) -> dict[str, Any]:
    response = _request(
        "POST",
        f"{BASE_URL}/auth/v1/token",
        params={"grant_type": "refresh_token"},
        headers=_public_headers(),
        json={"refresh_token": refresh_token},
    )

    if response.status_code >= 400:
        raise AuthError(401, "Your session expired. Please log in again.")

    return _json(response)


def get_user_from_token(token: str) -> dict[str, Any] | None:
    if not token:
        return None

    response = _request(
        "GET",
        f"{BASE_URL}/auth/v1/user",
        headers={
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {token}",
        },
    )

    if response.status_code >= 400:
        return None

    return _json(response)


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    response = _request(
        "GET",
        f"{BASE_URL}/auth/v1/admin/users/{user_id}",
        headers=_admin_headers(),
    )

    if response.status_code == 404:
        return None

    if response.status_code >= 400:
        raise AuthError(502, "Could not load the reporter's account.")

    return _json(response)


def update_profile(
    user_id: str,
    fields: dict[str, Any] | None = None,
    points_delta: int = 0,
) -> tuple[dict[str, Any], int]:
    """Merge fields into the user's metadata and optionally add credits.

    Returns the updated metadata and the new credit total.
    """

    user = get_user_by_id(user_id)
    metadata = dict((user or {}).get("user_metadata") or {})

    try:
        current_points = int(metadata.get("points") or 0)
    except (TypeError, ValueError):
        current_points = 0

    if fields:
        metadata.update(fields)

    total_points = max(current_points + points_delta, 0)
    metadata["points"] = total_points

    response = _request(
        "PUT",
        f"{BASE_URL}/auth/v1/admin/users/{user_id}",
        headers=_admin_headers(),
        json={"user_metadata": metadata},
    )

    if response.status_code >= 400:
        raise AuthError(502, "Could not update the member profile.")

    updated = _json(response)
    return dict(updated.get("user_metadata") or metadata), total_points


def contact_from_metadata(
    metadata: dict[str, Any], fallback_email: str = ""
) -> dict[str, str] | None:
    name = str(metadata.get("contact_name") or "").strip()
    email = str(metadata.get("contact_email") or "").strip() or fallback_email
    phone = str(metadata.get("contact_phone") or "").strip()

    if not name and not email and not phone:
        return None

    return {"name": name, "email": email, "phone": phone}


def build_profile(user: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(user.get("user_metadata") or {})
    email = str(user.get("email") or "")

    try:
        points = int(metadata.get("points") or 0)
    except (TypeError, ValueError):
        points = 0

    full_name = str(metadata.get("full_name") or "").strip()
    if not full_name:
        full_name = email.split("@")[0] if email else "LostLink member"

    return {
        "id": str(user.get("id") or ""),
        "email": email,
        "full_name": full_name,
        "points": points,
        "contact": contact_from_metadata(metadata, email),
        "created_at": user.get("created_at"),
    }


def session_payload(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "access_token": session.get("access_token"),
        "refresh_token": session.get("refresh_token"),
        "expires_in": session.get("expires_in"),
        "token_type": session.get("token_type") or "bearer",
    }
