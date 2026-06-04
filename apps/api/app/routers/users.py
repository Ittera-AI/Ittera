from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User

router = APIRouter()


class PublishingSettingsRequest(BaseModel):
    auto_post_enabled: bool


class PublishingSettingsResponse(BaseModel):
    auto_post_enabled: bool


@router.get("/me/publishing-settings", response_model=PublishingSettingsResponse)
async def get_publishing_settings(current_user: User = Depends(get_current_user)):
    return {"auto_post_enabled": bool(current_user.auto_post_enabled)}


@router.patch("/me/publishing-settings", response_model=PublishingSettingsResponse)
async def update_publishing_settings(
    payload: PublishingSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.auto_post_enabled = payload.auto_post_enabled
    db.commit()
    db.refresh(current_user)
    return {"auto_post_enabled": bool(current_user.auto_post_enabled)}
