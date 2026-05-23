from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_workspace_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.trends import TrendResponse
from app.services import trend_service

router = APIRouter()


@router.get("", response_model=TrendResponse)
async def get_trends(current_user: User = Depends(get_current_workspace_user), db: Session = Depends(get_db)):
    return trend_service.get_trends_for_user(db, current_user)


@router.post("/refresh", response_model=TrendResponse)
async def refresh_trends(current_user: User = Depends(get_current_workspace_user), db: Session = Depends(get_db)):
    return trend_service.refresh_trends(db, current_user)
