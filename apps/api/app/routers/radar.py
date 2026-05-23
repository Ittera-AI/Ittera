from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.radar import RadarInput, RadarOutput
from app.services.radar_service import RadarService

router = APIRouter()


@router.post("/scan", response_model=RadarOutput)
async def scan_trends(
    payload: RadarInput,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RadarService(db)
    return await service.scan(payload)
