"""
Context router — read and update the user's permanent context.

GET  /api/v1/context          → assembled context (all 3 layers) for the current user
GET  /api/v1/context/prompt   → the raw system prompt string (debugging / preview)
PATCH /api/v1/context         → update permanent context identity fields
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.schemas.context import AssembledContext, UpdatePermanentContextRequest
from app.services import context_service
from app.services.auth_service import _snapshot_user_context

router = APIRouter()


@router.get(
    "/",
    response_model=AssembledContext,
    summary="Get assembled context",
    description=(
        "Returns all three context layers — Permanent (identity + platform facts), "
        "Persona (AI-derived writing style), and Report (engagement insights) — "
        "merged into an AssembledContext with the ready-to-use system_prompt."
    ),
)
def get_context(
    platform: str = "linkedin",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssembledContext:
    return context_service.assemble(db, current_user, platform=platform)


@router.get(
    "/prompt",
    summary="Preview system prompt",
    description="Returns the raw LLM system prompt for the current user context. Useful for debugging.",
)
def get_system_prompt(
    platform: str = "linkedin",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    ctx = context_service.assemble(db, current_user, platform=platform)
    return {
        "system_prompt": ctx.system_prompt,
        "missing_layers": ctx.missing_layers,
        "context_version": ctx.permanent.context_version,
    }


@router.patch(
    "/",
    summary="Update permanent context",
    description=(
        "Updates the user's permanent context identity fields. "
        "Creates a new versioned UserContext snapshot so prior state is preserved."
    ),
)
def update_context(
    payload: UpdatePermanentContextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    # Update User row (fast-access denormalised copy)
    if payload.brand_name is not None:
        current_user.brand_name = payload.brand_name.strip()
    if payload.bio is not None:
        current_user.bio = payload.bio.strip()
    if payload.target_audience is not None:
        current_user.target_audience = payload.target_audience.strip()
    if payload.content_mission is not None:
        current_user.content_mission = payload.content_mission.strip()
    if payload.niche is not None:
        current_user.niche = payload.niche.strip()
    if payload.primary_platform is not None:
        current_user.primary_platform = payload.primary_platform

    db.commit()
    db.refresh(current_user)

    # Snapshot the new state (versioned, append-only)
    _snapshot_user_context(
        db,
        current_user,
        change_source="manual_edit",
        change_summary="User updated permanent context fields.",
    )

    ctx = context_service.assemble(db, current_user)
    return {
        "message": "Permanent context updated and snapshotted.",
        "context_version": ctx.permanent.context_version,
        "missing_layers": ctx.missing_layers,
    }
