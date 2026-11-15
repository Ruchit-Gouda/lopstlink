"""Report related API routes."""

import logging
import re
from datetime import date, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import (
    ALLOWED_IMAGE_TYPES,
    CONTACT_REVEAL_THRESHOLD,
    FOUND_REPORT_POINTS,
    LOST_REPORT_POINTS,
    MATCH_THRESHOLD,
    MAX_IMAGE_BYTES,
    STORAGE_BUCKET,
)
from app.database import supabase
from app.dependencies import get_current_user, get_optional_user
from app.schemas.report import MatchesResponse, ReportsResponse
from app.services.auth import (
    AuthError,
    build_profile,
    contact_from_metadata,
    get_user_by_id,
    is_valid_email,
    normalize_email,
    update_profile,
)
from app.services.matching import score_reports
from app.services.storage import attach_image_urls, with_image_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])

PHONE_RE = re.compile(r"^[0-9+()\-\s]{7,20}$")


def _clean_text(value: str, field: str, max_length: int) -> str:
    cleaned = value.strip()

    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail=f"{field} cannot be empty",
        )

    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"{field} must be {max_length} characters or fewer",
        )

    return cleaned


@router.post("/reports", status_code=201)
async def create_report(
    user: dict = Depends(get_current_user),
    report_type: str = Form(...),
    item_name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    color: str = Form(""),
    brand: str = Form(""),
    location_text: str = Form(...),
    event_date: date = Form(...),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    contact_phone: str = Form(""),
    image: UploadFile = File(...),
):
    if report_type not in ["lost", "found"]:
        raise HTTPException(
            status_code=400,
            detail="Report type must be lost or found",
        )

    extension = ALLOWED_IMAGE_TYPES.get(image.content_type or "")

    if not extension:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed",
        )

    # Allow one extra day so users in timezones ahead of the server are not
    # blocked from reporting something that happened "today" for them.
    if event_date > date.today() + timedelta(days=1):
        raise HTTPException(
            status_code=400,
            detail="The date cannot be in the future",
        )

    item_name = _clean_text(item_name, "Item name", 120)
    category = _clean_text(category, "Category", 80)
    description = _clean_text(description, "Description", 1000)
    location_text = _clean_text(location_text, "Location", 160)
    color = color.strip()[:60]
    brand = brand.strip()[:80]

    metadata = dict(user.get("user_metadata") or {})
    account_email = normalize_email(str(user.get("email") or ""))

    # The contact fields are what a matched member sees. Fall back to the
    # account details so a report always has a way to be claimed.
    contact_name = _clean_text(
        contact_name or str(metadata.get("full_name") or ""),
        "Contact name",
        120,
    )

    contact_email = normalize_email(contact_email or account_email)
    if not is_valid_email(contact_email):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid contact email address.",
        )

    contact_phone = contact_phone.strip()[:30]
    if contact_phone and not PHONE_RE.match(contact_phone):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid phone number, or leave it blank.",
        )

    image_data = await image.read()

    if len(image_data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 5 MB",
        )

    # Generate the filename ourselves so unusual client filenames cannot
    # break the storage path.
    image_path = f"{uuid4()}{extension}"
    user_id = str(user.get("id"))

    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            image_path,
            image_data,
            file_options={"content-type": image.content_type},
        )

        report_data = {
            "user_id": user_id,
            "report_type": report_type,
            "item_name": item_name,
            "category": category,
            "description": description,
            "color": color,
            "brand": brand,
            "location_text": location_text,
            "event_date": event_date.isoformat(),
            "image_path": image_path,
            "status": "open",
        }

        result = supabase.table("reports").insert(report_data).execute()

    except Exception as error:
        logger.exception("Report submission error: %s", error)

        # Remove the uploaded image when the database insert fails.
        try:
            supabase.storage.from_(STORAGE_BUCKET).remove([image_path])
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="Could not submit report. Please try again.",
        )

    awarded = FOUND_REPORT_POINTS if report_type == "found" else LOST_REPORT_POINTS
    total_points = int(metadata.get("points") or 0)
    updated_user = user

    try:
        updated_metadata, total_points = await run_in_threadpool(
            update_profile,
            user_id,
            {
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
            },
            awarded,
        )
        updated_user = dict(user)
        updated_user["user_metadata"] = updated_metadata
    except AuthError as error:
        # The report is already published, so do not fail the request. Credits
        # will simply be added on the next successful profile update.
        logger.warning("Could not update credits for %s: %s", user_id, error.detail)
        awarded = 0

    return {
        "message": "Report submitted successfully!",
        "report": with_image_url(result.data[0]),
        "credits": {
            "awarded": awarded,
            "total": total_points,
        },
        "user": build_profile(updated_user),
    }


@router.get("/reports", response_model=ReportsResponse)
def get_reports(report_type: str | None = Query(default=None)):
    if report_type and report_type not in ["lost", "found"]:
        raise HTTPException(
            status_code=400,
            detail="Report type must be lost or found",
        )

    try:
        query = supabase.table("reports").select("*").eq("status", "open")

        if report_type:
            query = query.eq("report_type", report_type)

        result = query.order("created_at", desc=True).execute()

        return {"reports": attach_image_urls(result.data or [])}

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Report retrieval error: %s", error)
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve reports.",
        )


@router.get("/matches/{report_id}", response_model=MatchesResponse)
def get_matches(
    report_id: UUID,
    min_score: float = Query(default=MATCH_THRESHOLD, ge=0, le=100),
    limit: int = Query(default=20, ge=1, le=100),
    viewer: dict | None = Depends(get_optional_user),
):
    report_id = str(report_id)

    try:
        selected_result = (
            supabase.table("reports")
            .select("*")
            .eq("id", report_id)
            .eq("status", "open")
            .execute()
        )

        if not selected_result.data:
            raise HTTPException(status_code=404, detail="Report not found")

        selected_report = selected_result.data[0]

        viewer_id = str(viewer.get("id") or "") if viewer else ""
        viewer_is_owner = bool(viewer_id) and viewer_id == str(
            selected_report.get("user_id") or ""
        )

        opposite_type = (
            "found" if selected_report["report_type"] == "lost" else "lost"
        )

        other_result = (
            supabase.table("reports")
            .select("*")
            .eq("report_type", opposite_type)
            .eq("status", "open")
            .execute()
        )

        scored = []

        for other_report in other_result.data or []:
            result = score_reports(selected_report, other_report)

            if result["score"] < min_score:
                continue

            scored.append(
                {
                    "report": other_report,
                    "similarity_score": result["score"],
                    "match_reasons": result["reasons"],
                    "contact_available": result["score"]
                    >= CONTACT_REVEAL_THRESHOLD,
                    "contact_unlocked": False,
                    "contact": None,
                }
            )

        scored.sort(
            key=lambda item: item["similarity_score"],
            reverse=True,
        )

        scored = scored[:limit]

        # Fetch each reporter once, then release contact details only when the
        # viewer owns the selected report and the pair scores high enough.
        # This keeps email addresses between the two matched members.
        unlocked_ids = {
            item["report"].get("user_id")
            for item in scored
            if item["contact_available"]
            and viewer_is_owner
            and item["report"].get("user_id")
        }

        reporters: dict[str, dict | None] = {}

        for user_id in unlocked_ids:
            try:
                reporters[user_id] = get_user_by_id(user_id)
            except AuthError:
                reporters[user_id] = None

        for item in scored:
            unlocked = item["contact_available"] and viewer_is_owner
            item["contact_unlocked"] = unlocked

            if not unlocked:
                continue

            reporter = reporters.get(item["report"].get("user_id") or "")

            if reporter:
                item["contact"] = contact_from_metadata(
                    dict(reporter.get("user_metadata") or {}),
                    str(reporter.get("email") or ""),
                )

        # Sign all images with a single storage request.
        reports = attach_image_urls(
            [selected_report] + [item["report"] for item in scored]
        )
        signed = {report["id"]: report for report in reports}

        for item in scored:
            item["report"] = signed[item["report"]["id"]]

        return {
            "selected_report": signed[selected_report["id"]],
            "matches": scored,
            "contact_threshold": CONTACT_REVEAL_THRESHOLD,
            "viewer_is_owner": viewer_is_owner,
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Matching error: %s", error)
        raise HTTPException(
            status_code=500,
            detail="Could not find matching reports.",
        )
