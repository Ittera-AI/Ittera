from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.linkedin import LinkedInConnectResponse, LinkedInStatusResponse, LinkedInSyncResponse
from app.services import linkedin_service

router = APIRouter()


@router.get("/status", response_model=LinkedInStatusResponse)
async def status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return linkedin_service.get_status(db, current_user)
    except (OperationalError, ProgrammingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database schema is out of date. Run `alembic upgrade head` in apps/api.",
        ) from exc


@router.post("/connect/mock", response_model=LinkedInConnectResponse)
async def connect_mock(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return linkedin_service.connect_mock(db, current_user)


@router.post("/sync", response_model=LinkedInSyncResponse)
async def sync(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return linkedin_service.sync_mock_posts(db, current_user)
