"""Request and response models for accounts, credits and contact details."""

from pydantic import BaseModel, Field


class ContactOut(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""


class ProfileOut(BaseModel):
    id: str
    email: str
    full_name: str
    points: int
    contact: ContactOut | None = None
    created_at: str | None = None


class SessionOut(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int | None = None
    token_type: str = "bearer"


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=4096)


class AuthResponse(BaseModel):
    session: SessionOut
    user: ProfileOut


class MeResponse(BaseModel):
    user: ProfileOut
