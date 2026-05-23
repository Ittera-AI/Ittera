from pydantic import BaseModel, Field


class ContentSlot(BaseModel):
    date: str
    platform: str
    content_type: str
    topic: str
    goal: str


class CalendarInput(BaseModel):
    niche: str = Field(min_length=1, max_length=160)
    platforms: list[str] = Field(default_factory=list, max_length=5)
    posting_frequency: int = Field(ge=1, le=31)
    historical_posts: list[str] = Field(default_factory=list, max_length=100)


class CalendarOutput(BaseModel):
    content_plan: list[ContentSlot]
