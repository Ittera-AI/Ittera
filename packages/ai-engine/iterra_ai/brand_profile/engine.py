"""BrandProfileEngine — derives writing style from real post data via Anthropic Claude."""

from __future__ import annotations

import os
import statistics

from iterra_ai.brand_profile.schemas import BrandProfileInput, BrandProfileOutput
from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.prompts.brand_profile import BRAND_PROFILE_V1, SYSTEM_PROMPT


class BrandProfileEngine(BaseEngine[BrandProfileInput, BrandProfileOutput]):
    """
    Analyses a creator's posts and returns a structured brand profile.

    Input posts are expected to be pre-formatted annotation strings:
        "Post #N | YYYY-MM-DD | Engagement: X.X%\\n{content}"

    Falls back to a deterministic mock if ANTHROPIC_API_KEY is not set.
    """

    def generate(self, input: BrandProfileInput) -> BrandProfileOutput:  # noqa: A002
        if not os.getenv("ANTHROPIC_API_KEY"):
            return self._mock_output(input)

        posts_block = "\n\n".join(input.posts)
        raw = self._call_llm(
            system=SYSTEM_PROMPT,
            user=BRAND_PROFILE_V1.format(niche=input.niche, posts=posts_block),
        )
        return self._parse_json_output(raw, BrandProfileOutput)

    # ── Fallback (no API key) ─────────────────────────────────────────────────

    def _mock_output(self, input: BrandProfileInput) -> BrandProfileOutput:
        """Deterministic fallback used in development when no Anthropic key is set."""
        # Compute avg post length from the formatted post strings if available
        raw_bodies = [p.split("\n", 1)[-1] for p in input.posts if "\n" in p]
        avg_len: int | None = None
        if raw_bodies:
            try:
                avg_len = int(statistics.median(len(b) for b in raw_bodies))
            except Exception:
                avg_len = None

        return BrandProfileOutput(
            voice_tone="Clear, analytical, and calmly opinionated",
            audience=f"Professionals interested in {input.niche or 'AI-powered content systems'}",
            core_topics=["content systems", "trend interpretation", "performance learning"],
            writing_patterns=[
                "Opens with a direct observation",
                "Uses short paragraphs for pace",
                "Connects strategy to operating habits",
            ],
            content_pillars=["Strategic clarity", "Repeatable systems", "Performance learning"],
            hashtag_strategy="#ContentStrategy #LinkedInGrowth #AIWorkflow",
            summary=(
                "A practical strategy voice that turns noisy signals into useful content decisions."
            ),
            avg_post_length=avg_len,
            emoji_usage="none",
        )
