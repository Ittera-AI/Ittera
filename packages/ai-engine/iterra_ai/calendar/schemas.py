from pydantic import BaseModel


class ContentSlot(BaseModel):
    date: str
    platform: str
    content_type: str
    topic: str
    goal: str


class CalendarInput(BaseModel):
    niche: str
    platforms: list[str]
    posting_frequency: int
    historical_posts: list[str] = []


class CalendarOutput(BaseModel):
    content_plan: list[ContentSlot]
