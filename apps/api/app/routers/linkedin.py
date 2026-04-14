from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.linkedin import LinkedInConnectResponse, LinkedInStatusResponse, LinkedInSyncResponse
from app.services import linkedin_service

router = APIRouter()


@router.get("/status", response_model=LinkedInStatusResponse)
async def status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return linkedin_service.get_status(db, current_user)


@router.post("/connect/mock", response_model=LinkedInConnectResponse)
async def connect_mock(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return linkedin_service.connect_mock(db, current_user)


@router.post("/sync", response_model=LinkedInSyncResponse)
async def sync(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return linkedin_service.sync_mock_posts(db, current_user)
