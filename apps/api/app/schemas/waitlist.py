from datetime import datetime

from pydantic import BaseModel, EmailStr


class WaitlistRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    profession: str | None = None


class WaitlistStatsResponse(BaseModel):
    total_joined: int
    total_seats: int
    remaining_seats: int
    recent_joiners: list[str]


class WaitlistMemberStatusResponse(BaseModel):
    email: str
    joined: bool
    access_approved: bool
    approved_at: datetime | None = None
    position: int | None
    total_joined: int
    total_seats: int
    remaining_seats: int


class WaitlistResponse(BaseModel):
    message: str
    position: int
    already_joined: bool
    access_approved: bool
    total_joined: int
    total_seats: int
    remaining_seats: int
    recent_joiners: list[str]


class WaitlistApprovalRequest(BaseModel):
    email: EmailStr


class WaitlistApprovalResponse(BaseModel):
    email: str
    access_approved: bool
    approved_at: datetime | None = None
    approved_by: str | None = None
    message: str


class WaitlistEntryResponse(BaseModel):
    email: str
    name: str | None = None
    profession: str | None = None
    access_approved: bool
    approved_at: datetime | None = None
    approved_by: str | None = None
    created_at: datetime


class WaitlistAdminListResponse(BaseModel):
    entries: list[WaitlistEntryResponse]
