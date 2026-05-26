from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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

    # Permanent context identity fields
    brand_name: str | None = None
    bio: str | None = None
    target_audience: str | None = None
    content_mission: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingRequest(BaseModel):
    full_name: str
    niche: str
    goals: str | None = None
    primary_platform: str = "linkedin"
    storage_preference: str = "google_drive"  # "google_drive" | "local" | "iterra"

    # Permanent context — the rich identity layer
    brand_name: str | None = None           # Brand or personal name used in content
    bio: str | None = None                  # 2–4 sentence bio in the user's own words
    target_audience: str | None = None      # Who the content is created for
    content_mission: str | None = None      # Why they create content / what change they drive
