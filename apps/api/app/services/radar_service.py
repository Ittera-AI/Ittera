from sqlalchemy.orm import Session

from app.schemas.radar import RadarInput, RadarOutput


class RadarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def scan(self, input: RadarInput) -> RadarOutput:
        # TODO: wire up iterra_ai.radar.TrendRadar
        raise NotImplementedError("RadarService.scan is not yet implemented")
