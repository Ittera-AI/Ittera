from sqlalchemy.orm import Session

from app.schemas.repurpose import RepurposeInput, RepurposeOutput


class RepurposeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    async def repurpose(self, input: RepurposeInput) -> RepurposeOutput:
        from iterra_ai.repurpose.engine import RepurposeEngine
        from iterra_ai.repurpose.schemas import RepurposeInput as EngineRepurposeInput

        engine = RepurposeEngine()
        engine_in = EngineRepurposeInput.model_validate(input.model_dump())
        out = engine.generate(engine_in)
        return RepurposeOutput.model_validate(out.model_dump())
