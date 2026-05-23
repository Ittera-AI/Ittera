from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_workspace_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.auth import OnboardingRequest, UserResponse
from app.services import auth_service

router = APIRouter()


@router.post("", response_model=UserResponse)
async def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return auth_service.complete_onboarding(db, current_user, payload)
