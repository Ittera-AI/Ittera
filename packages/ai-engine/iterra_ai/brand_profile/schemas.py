from pydantic import BaseModel


class BrandProfileInput(BaseModel):
    niche: str
    posts: list[str]


class BrandProfileOutput(BaseModel):
    voice_tone: str
    audience: str
    core_topics: list[str]
    writing_patterns: list[str]
    content_pillars: list[str]
    hashtag_strategy: str
    summary: str
