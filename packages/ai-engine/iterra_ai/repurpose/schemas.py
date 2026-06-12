from pydantic import BaseModel


class RepurposedItem(BaseModel):
    platform: str
    content: str
    format: str


class RepurposeInput(BaseModel):
    original_content: str
    source_platform: str
    target_platforms: list[str]
    max_chars: int | None = None  # Tier-aware character limit for target platform
    system_prompt: str | None = None  # Brand voice context for voice consistency


class RepurposeOutput(BaseModel):
    repurposed: list[RepurposedItem]
