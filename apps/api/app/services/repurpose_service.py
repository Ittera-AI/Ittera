from sqlalchemy.orm import Session

from app.schemas.repurpose import RepurposeInput, RepurposeOutput


class RepurposeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def repurpose(self, input: RepurposeInput) -> RepurposeOutput:
        # TODO: wire up iterra_ai.repurpose.RepurposeEngine
        raise NotImplementedError("RepurposeService.repurpose is not yet implemented")
