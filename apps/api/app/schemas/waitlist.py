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
