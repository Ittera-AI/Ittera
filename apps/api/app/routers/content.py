from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.config import settings
from app.models.user import User
from app.schemas.content import (
    CalendarEventResponse,
    DraftMediaResponse,
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
    return await content_service.publish_now(db, current_user, payload.draft_id)


@router.post("/drafts/{draft_id}/publish-now", response_model=PublishResponse)
async def publish_draft_now(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await content_service.publish_now(db, current_user, draft_id)


@router.post("/schedule", response_model=ScheduleResponse)
async def schedule(payload: ScheduleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.schedule_post(db, current_user, payload)


@router.delete("/schedule/{draft_id}")
async def cancel_schedule(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.cancel_schedule(db, current_user, draft_id)


@router.post("/drafts/{draft_id}/approve", response_model=DraftResponse)
async def approve_draft(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.approve_draft(db, current_user, draft_id)


@router.post("/drafts/{draft_id}/media", response_model=DraftMediaResponse)
async def add_draft_media(
    draft_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await _read_upload_file(file)
    return content_service.add_media_to_draft(
        db,
        current_user,
        draft_id,
        file.filename or "image",
        file.content_type or "application/octet-stream",
        content,
    )


@router.delete("/drafts/{draft_id}/media/{media_id}")
async def delete_draft_media(
    draft_id: str,
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return content_service.delete_media(db, current_user, draft_id, media_id)


@router.get("/media-file/{media_id}")
async def media_file(
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    media = content_service.get_media_file(db, current_user, media_id)
    return FileResponse(Path(media.local_path), media_type=media.mime_type, filename=media.filename)


@router.get("/calendar", response_model=list[CalendarEventResponse])
async def calendar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return content_service.calendar_events(db, current_user)


async def _read_upload_file(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.MEDIA_MAX_BYTES:
            limit_mb = max(1, settings.MEDIA_MAX_BYTES // (1024 * 1024))
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Image must be {limit_mb}MB or smaller.")
        chunks.append(chunk)
    return b"".join(chunks)
