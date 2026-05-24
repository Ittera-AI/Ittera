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
    access_approved: bool = False
    approved_at: datetime | None = None
    position: int | None
    total_joined: int
    total_seats: int
    remaining_seats: int


class WaitlistResponse(BaseModel):
    message: str
    position: int
    already_joined: bool
    total_joined: int
    total_seats: int
    remaining_seats: int
    recent_joiners: list[str]


class WaitlistAdminActionRequest(BaseModel):
    email: EmailStr


class WaitlistAdminEntryResponse(BaseModel):
    email: str
    name: str | None
    profession: str | None
    access_approved: bool
    approved_at: datetime | None
    approved_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WaitlistAdminEntriesResponse(BaseModel):
    entries: list[WaitlistAdminEntryResponse]
