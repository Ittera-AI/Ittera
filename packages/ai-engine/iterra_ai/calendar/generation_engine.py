from pydantic import BaseModel


class GenerationInput(BaseModel):
    brand_profile: dict
    platform: str
    user_prompt: str
    trend_context: str | None = None


class GenerationOutput(BaseModel):
    content: str
    word_count: int
    estimated_read_time_seconds: int
    platform_char_count: int
    within_platform_limit: bool


class ContentGenerationEngine:
    def generate(self, input: GenerationInput) -> GenerationOutput:
        content = (
            f"{input.user_prompt}\n\n"
            "The useful version is not more content. It is a better loop: signal, draft, "
            "review, publish, learn.\n\nThat is where strategy starts to compound."
        )
        limit = {"linkedin": 3000, "instagram": 2200, "twitter": 280}.get(input.platform, 3000)
        return GenerationOutput(
            content=content,
            word_count=len(content.split()),
            estimated_read_time_seconds=max(10, len(content.split()) // 3),
            platform_char_count=len(content),
            within_platform_limit=len(content) <= limit,
        )
