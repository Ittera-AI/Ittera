from pydantic import BaseModel

class ContentGenerationInput(BaseModel):
    platform: str
    prompt: str
    hook: str | None = None
    system_prompt: str
    platform_rules: dict

class ContentGenerationOutput(BaseModel):
    content: str
    model: str
    is_mock: bool
    word_count: int
    char_count: int
