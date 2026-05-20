from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.schemas.calendar import CalendarInput, CalendarOutput
from app.services.calendar_service import CalendarService

router = APIRouter()


@router.post(
    "/generate",
    response_model=CalendarOutput,
    summary="Generate content calendar",
    description=(
        "Produces a structured weekly-style plan. "
        "By default this is a deterministic mock plan suitable for demos and CI. "
        "Set `USE_ITERRA_AI_CALENDAR=true` with `ANTHROPIC_API_KEY` configured to use "
        "`iterra_ai.CalendarEngine` (falls back to mock on LLM failure)."
    ),
)
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
