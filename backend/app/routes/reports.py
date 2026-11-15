"""Report related API routes."""

import logging
from datetime import date, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.config import (
    ALLOWED_IMAGE_TYPES,
    MATCH_THRESHOLD,
    MAX_IMAGE_BYTES,
    STORAGE_BUCKET,
)
from app.database import supabase
from app.schemas.report import (
    MatchesResponse,
    ReportsResponse,
    StatusResponse,
    StatusUpdate,
)
from app.services.matching import score_reports
from app.services.storage import attach_image_urls, with_image_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])


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
    report_type: str = Form(...),
    item_name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    color: str = Form(""),
    brand: str = Form(""),
    location_text: str = Form(...),
    event_date: date = Form(...),
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

    image_data = await image.read()

    if len(image_data) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="Image must be smaller than 5 MB",
        )

    # Generate the filename ourselves so unusual client filenames cannot
    # break the storage path.
    image_path = f"{uuid4()}{extension}"

    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            image_path,
            image_data,
            file_options={"content-type": image.content_type},
        )

        report_data = {
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

        return {
            "message": "Report submitted successfully!",
            "report": with_image_url(result.data[0]),
        }

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


@router.get("/reports", response_model=ReportsResponse)
def get_reports(report_type: str | None = Query(default=None)):
    if report_type and report_type not in ["lost", "found"]:
        raise HTTPException(
            status_code=400,
            detail="Report type must be lost or found",
        )

    try:
        query = (
            supabase.table("reports")
            .select("*")
            .eq("status", "open")
        )

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
                }
            )

        scored.sort(
            key=lambda item: item["similarity_score"],
            reverse=True,
        )

        # Sign all images with a single storage request.
        reports = attach_image_urls(
            [selected_report] + [item["report"] for item in scored[:limit]]
        )
        signed = {report["id"]: report for report in reports}

        for item in scored[:limit]:
            item["report"] = signed[item["report"]["id"]]

        return {
            "selected_report": signed[selected_report["id"]],
            "matches": scored[:limit],
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Matching error: %s", error)
        raise HTTPException(
            status_code=500,
            detail="Could not find matching reports.",
        )


@router.patch("/reports/{report_id}/status", response_model=StatusResponse)
def update_report_status(report_id: UUID, payload: StatusUpdate):
    report_id = str(report_id)

    try:
        existing = (
            supabase.table("reports")
            .select("id")
            .eq("id", report_id)
            .execute()
        )

        if not existing.data:
            raise HTTPException(status_code=404, detail="Report not found")

        result = (
            supabase.table("reports")
            .update({"status": payload.status})
            .eq("id", report_id)
            .execute()
        )

        return {
            "message": f"Report marked as {payload.status}.",
            "report": with_image_url(result.data[0]),
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Status update error: %s", error)
        raise HTTPException(
            status_code=500,
            detail="Could not update the report.",
        )
