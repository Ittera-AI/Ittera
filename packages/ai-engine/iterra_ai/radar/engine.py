"""EXPERIMENTAL — synthetic trends until real signal ingestion is wired."""

from datetime import datetime, timezone

from iterra_ai.core.base_engine import BaseEngine
from iterra_ai.radar.schemas import RadarInput, RadarOutput, TrendItem


class TrendRadar(BaseEngine[RadarInput, RadarOutput]):
    """Scans and surfaces trending topics relevant to a given niche.

    TODO: Implement using web search APIs + LLM summarization.
    See prompts/radar.py for prompt templates.
    """

    def scan(self, input: RadarInput) -> RadarOutput:
        trends = [
            TrendItem(
                topic=f"{input.niche.title()} operating loops",
                score=9.2,
                platforms=input.platforms,
                summary="Creators are shifting from one-off posts to repeatable content systems.",
            ),
            TrendItem(
                topic="AI-assisted review",
                score=8.7,
                platforms=input.platforms,
                summary="Teams want speed without losing human taste and approval.",
            ),
        ][: input.limit]
        return RadarOutput(trends=trends, scanned_at=datetime.now(timezone.utc))

    def generate(self, input: RadarInput) -> RadarOutput:
        return self.scan(input)
