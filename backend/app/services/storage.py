"""Helpers for working with the private Supabase storage bucket."""

import logging
from typing import Any, Iterable

from app.config import IMAGE_URL_TTL, STORAGE_BUCKET
from app.database import supabase

logger = logging.getLogger(__name__)


def signed_image_urls(image_paths: Iterable[str | None]) -> dict[str, str]:
    """Return a mapping of storage path -> temporary signed URL."""

    paths = [path for path in dict.fromkeys(image_paths) if path]

    if not paths:
        return {}

    try:
        results = supabase.storage.from_(STORAGE_BUCKET).create_signed_urls(
            paths,
            IMAGE_URL_TTL,
        )
    except Exception as error:  # pragma: no cover - network failure
        logger.warning("Could not create signed image URLs: %s", error)
        return {}

    urls: dict[str, str] = {}

    for item in results or []:
        url = item.get("signedURL") or item.get("signedUrl")
        if url and item.get("path"):
            urls[item["path"]] = url

    return urls


def with_image_url(report: dict[str, Any]) -> dict[str, Any]:
    """Attach an image_url field to a single report."""

    return attach_image_urls([report])[0]


def attach_image_urls(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach image_url fields to a list of reports with one batch request."""

    urls = signed_image_urls(report.get("image_path") for report in reports)

    return [
        {**report, "image_url": urls.get(report.get("image_path"))}
        for report in reports
    ]
