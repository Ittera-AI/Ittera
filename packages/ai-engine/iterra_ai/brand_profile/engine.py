import os

from iterra_ai.brand_profile.schemas import BrandProfileInput, BrandProfileOutput
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.prompts.brand_profile import BRAND_PROFILE_V1, SYSTEM_PROMPT


class BrandProfileEngine(BaseEngine[BrandProfileInput, BrandProfileOutput]):
    def generate(self, input: BrandProfileInput) -> BrandProfileOutput:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return BrandProfileOutput(
                voice_tone="Clear, analytical, and calmly opinionated",
                audience=f"Professionals interested in {input.niche}",
                core_topics=["content systems", "trend interpretation", "performance learning"],
                writing_patterns=["direct hook", "short paragraphs", "practical closing insight"],
                content_pillars=["strategy", "creation", "analysis"],
                hashtag_strategy="#ContentStrategy #AIWorkflow #LinkedInGrowth",
                summary=(
                    "A practical strategy voice that turns noisy signals into useful "
                    "content decisions."
                ),
            )
        raw = self._call_llm(
            system=SYSTEM_PROMPT,
            user=BRAND_PROFILE_V1.format(niche=input.niche, posts="\n\n".join(input.posts)),
        )
        return self._parse_json_output(raw, BrandProfileOutput)
