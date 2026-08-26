from typing import Any

from pydantic import BaseModel


class ContentGenerationInput(BaseModel):
    platform: str
    prompt: str
    hook: str | None = None
    system_prompt: str
    platform_rules: dict[str, Any]

class ContentGenerationOutput(BaseModel):
    content: str
    model: str
    is_mock: bool
    word_count: int
    char_count: int
