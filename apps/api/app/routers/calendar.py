from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.calendar import CalendarInput, CalendarOutput
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.post("/generate", response_model=CalendarOutput)
async def generate_calendar(
    payload: CalendarInput,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.generate(payload)


@router.get("/", response_model=list[CalendarOutput])
async def list_calendars(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = CalendarService(db)
    return await service.list(user_id=current_user.id)
