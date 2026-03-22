from sqlalchemy.orm import Session

from app.schemas.calendar import CalendarInput, CalendarOutput


class CalendarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def generate(self, input: CalendarInput) -> CalendarOutput:
        # TODO: wire up iterra_ai.calendar.CalendarEngine
        raise NotImplementedError("CalendarService.generate is not yet implemented")

    async def list(self, user_id: str) -> list[CalendarOutput]:
        # TODO: fetch from database
        return []
