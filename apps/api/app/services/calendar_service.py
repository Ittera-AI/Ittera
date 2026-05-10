import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.calendar import CalendarInput, CalendarOutput, ContentSlot

logger = logging.getLogger(__name__)


class CalendarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def generate(self, input: CalendarInput) -> CalendarOutput:
        if settings.USE_ITERRA_AI_CALENDAR and settings.ANTHROPIC_API_KEY:
            try:
                from iterra_ai.calendar.engine import CalendarEngine
                from iterra_ai.calendar.schemas import CalendarInput as EngineCalendarInput

                engine = CalendarEngine()
                engine_in = EngineCalendarInput.model_validate(input.model_dump())
                engine_out = engine.generate(engine_in)
                return CalendarOutput.model_validate(engine_out.model_dump())
            except Exception as exc:
                logger.warning("CalendarEngine failed; falling back to mock plan: %s", exc)

        plan: list[ContentSlot] = []
        platforms = input.platforms or ["linkedin"]
        frequency = max(1, input.posting_frequency)

        for idx in range(frequency):
            platform = platforms[idx % len(platforms)]
            plan.append(
                ContentSlot(
                    date=f"Day {idx + 1}",
                    platform=platform,
                    content_type="insight-post",
                    topic=f"{input.niche} angle {idx + 1}",
                    goal="Build audience trust with clear tactical insight.",
                )
            )

        return CalendarOutput(content_plan=plan)

    async def list(self, user_id: str) -> list[CalendarOutput]:
        # TODO: fetch from database
        return []
