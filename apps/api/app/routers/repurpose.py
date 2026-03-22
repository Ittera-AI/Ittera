from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.repurpose import RepurposeInput, RepurposeOutput
from app.services.repurpose_service import RepurposeService

router = APIRouter()


@router.post("/", response_model=RepurposeOutput)
async def repurpose_content(
    payload: RepurposeInput,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = RepurposeService(db)
    return await service.repurpose(payload)
