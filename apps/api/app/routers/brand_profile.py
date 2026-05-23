from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_workspace_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.brand_profile import (
    BrandProfileGenerateResponse,
    BrandProfileResponse,
    BrandProfileUpdateRequest,
)
from app.services import brand_profile_service

router = APIRouter()


@router.get("", response_model=BrandProfileResponse)
async def get_profile(current_user: User = Depends(get_current_workspace_user), db: Session = Depends(get_db)):
    try:
        return brand_profile_service.get_profile(db, current_user)
    except (OperationalError, ProgrammingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database schema is out of date. Run `alembic upgrade head` in apps/api.",
        ) from exc


@router.post("/generate", response_model=BrandProfileGenerateResponse)
async def generate_profile(current_user: User = Depends(get_current_workspace_user), db: Session = Depends(get_db)):
    return brand_profile_service.generate_profile(db, current_user)


@router.patch("", response_model=BrandProfileResponse)
async def update_profile(
    payload: BrandProfileUpdateRequest,
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    return brand_profile_service.update_profile(db, current_user, payload.profile)


@router.post("/confirm", response_model=BrandProfileResponse)
async def confirm_profile(current_user: User = Depends(get_current_workspace_user), db: Session = Depends(get_db)):
    return brand_profile_service.confirm_profile(db, current_user)
