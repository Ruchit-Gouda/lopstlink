"""Pydantic models used by the API responses."""

from typing import Literal

from pydantic import BaseModel

from app.schemas.auth import ContactOut


class ReportOut(BaseModel):
    id: str
    report_type: Literal["lost", "found"]
    item_name: str
    category: str
    description: str
    color: str | None = None
    brand: str | None = None
    location_text: str
    event_date: str
    image_path: str | None = None
    image_url: str | None = None
    status: str
    created_at: str | None = None
    user_id: str | None = None


class ReportsResponse(BaseModel):
    reports: list[ReportOut]


class MatchOut(BaseModel):
    report: ReportOut
    similarity_score: float
    match_reasons: list[str] = []
    contact_available: bool = False
    contact_unlocked: bool = False
    contact: ContactOut | None = None


class MatchesResponse(BaseModel):
    selected_report: ReportOut
    matches: list[MatchOut]
    contact_threshold: float = 70
    viewer_is_owner: bool = False
