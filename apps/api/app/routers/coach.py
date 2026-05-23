from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.coach import CoachInput, CoachOutput
from app.services.coach_service import CoachService

router = APIRouter()


@router.post("/analyze", response_model=CoachOutput)
async def analyze_content(
    payload: CoachInput,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CoachService(db)
    return await service.analyze(payload)
