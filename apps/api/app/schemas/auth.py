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
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class OnboardingRequest(BaseModel):
    full_name: str
    niche: str
    goals: str | None = None
    primary_platform: str = "linkedin"
