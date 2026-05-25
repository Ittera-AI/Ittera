from __future__ import annotations

from pydantic import BaseModel, Field


class BrandProfileInput(BaseModel):
    niche: str
    # Each entry is a pre-formatted string:
    # "Post #N | YYYY-MM-DD | Engagement: X.X%\n{content}"
    posts: list[str]


class BrandProfileOutput(BaseModel):
    voice_tone: str
    audience: str
    core_topics: list[str]
    writing_patterns: list[str]
    content_pillars: list[str]
    hashtag_strategy: str
    summary: str
    # Optional fields populated when real posts are analysed
    avg_post_length: int | None = Field(
        default=None,
        description="Median character count of the analysed posts",
    )
    emoji_usage: str | None = Field(
        default=None,
        description="Brief characterisation, e.g. 'none', 'occasional', 'frequent'",
    )
