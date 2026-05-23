from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    full_name: str | None = None
    niche: str | None = None
    goals: str | None = None
    primary_platform: str = "linkedin"
    onboarding_complete: bool = False
    storage_preference: str = "google_drive"
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class WorkspaceAccessResponse(BaseModel):
    email: str
    has_access: bool
    waitlisted: bool
    access_approved: bool
    is_admin: bool
    approved_at: str | None = None
    reason: str | None = None


class OnboardingRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    niche: str | None = Field(default=None, max_length=160)
    goals: str | None = Field(default=None, max_length=1000)
    primary_platform: Literal["linkedin", "instagram", "twitter"] = "linkedin"
    storage_preference: Literal["google_drive", "local", "iterra"] = "google_drive"
