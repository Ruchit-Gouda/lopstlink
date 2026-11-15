"""Shared Supabase client for database and storage access."""

from supabase import create_client

from app.config import SUPABASE_SERVICE_KEY, SUPABASE_URL

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
