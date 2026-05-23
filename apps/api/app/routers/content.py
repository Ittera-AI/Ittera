from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.content import (
    CalendarEventResponse,
    DraftResponse,
    DraftUpdateRequest,
    GenerateRequest,
    GenerateResponse,
    PublishRequest,
    PublishResponse,
    RepurposeRequest,
    RepurposeResponse,
    ScheduleRequest,
    ScheduleResponse,
    SuggestRequest,
    SuggestResponse,
)
from app.services import content_service

router = APIRouter()


@router.post("/suggest", response_model=SuggestResponse)
async def suggest(payload: SuggestRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.suggest(db, current_user, payload)


@router.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.generate(db, current_user, payload)


@router.post("/repurpose", response_model=RepurposeResponse)
async def repurpose(payload: RepurposeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.repurpose(db, current_user, payload)


@router.get("/drafts", response_model=list[DraftResponse])
async def list_drafts(
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return content_service.list_drafts(db, current_user, status)


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.get_draft(db, current_user, draft_id)


@router.patch("/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(
    draft_id: str,
    payload: DraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return content_service.update_draft(db, current_user, draft_id, payload)


@router.post("/publish", response_model=PublishResponse)
async def publish(payload: PublishRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.publish_now(db, current_user, payload.draft_id)


@router.post("/schedule", response_model=ScheduleResponse)
async def schedule(payload: ScheduleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.schedule_post(db, current_user, payload)


@router.delete("/schedule/{draft_id}")
async def cancel_schedule(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.cancel_schedule(db, current_user, draft_id)


@router.get("/calendar", response_model=list[CalendarEventResponse])
async def calendar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.calendar_events(db, current_user)
