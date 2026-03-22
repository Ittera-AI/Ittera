from sqlalchemy.orm import Session

from app.schemas.coach import CoachInput, CoachOutput


class CoachService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def analyze(self, input: CoachInput) -> CoachOutput:
        # TODO: wire up iterra_ai.coach.EngagementCoach
        raise NotImplementedError("CoachService.analyze is not yet implemented")
