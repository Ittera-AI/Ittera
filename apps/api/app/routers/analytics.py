from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.analytics import PostAnalysisResponse, PostWithAnalysis
from app.services import analytics_service

router = APIRouter()


@router.get("/posts", response_model=list[PostWithAnalysis])
async def posts(
    limit: int = Query(default=20, ge=1, le=100),
    platform: str = "linkedin",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return analytics_service.posts_with_analysis(db, current_user, limit, platform)


@router.post("/analyze/{post_id}", response_model=PostAnalysisResponse)
async def analyze(post_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analytics_service.analyze_post(db, current_user, post_id)
