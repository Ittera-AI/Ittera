from pydantic import BaseModel


class CoachInput(BaseModel):
    content: str
    platform: str
    goal: str | None = None


class CoachOutput(BaseModel):
    score: float
    suggestions: list[str]
    summary: str
