from pydantic import BaseModel, Field


class CoachInput(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    platform: str = Field(min_length=1, max_length=40)
    goal: str | None = Field(default=None, max_length=500)


class CoachOutput(BaseModel):
    score: float
    suggestions: list[str]
    summary: str
