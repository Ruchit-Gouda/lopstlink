"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "Supabase credentials are missing. Please copy backend/.env.example "
        "to backend/.env and fill in SUPABASE_URL and SUPABASE_SERVICE_KEY."
    )

STORAGE_BUCKET = os.getenv("STORAGE_BUCKET", "item-images")

# Signed URLs are generated on every API request. One day is long enough for
# the browser to cache the image while keeping the private bucket protected.
IMAGE_URL_TTL = int(os.getenv("IMAGE_URL_TTL", "86400"))

# Reports below this similarity score are not returned as matches.
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "25"))

# Contact details are only released when two reports score at least this much.
CONTACT_REVEAL_THRESHOLD = float(os.getenv("CONTACT_REVEAL_THRESHOLD", "70"))

# Link credits earned for publishing a report.
LOST_REPORT_POINTS = int(os.getenv("LOST_REPORT_POINTS", "10"))
FOUND_REPORT_POINTS = int(os.getenv("FOUND_REPORT_POINTS", "15"))

_default_origins = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:5174,http://127.0.0.1:5174"
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
