from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.datetime_helpers import utc_now
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.models.waitlist import WaitlistEntry
from app.schemas.waitlist import (
    WaitlistAdminActionRequest,
    WaitlistAdminEntriesResponse,
    WaitlistAdminEntryResponse,
    WaitlistMemberStatusResponse,
    WaitlistRequest,
    WaitlistResponse,
    WaitlistStatsResponse,
)
from app.services.email import send_waitlist_confirmation_email

router = APIRouter()


def _admin_emails() -> set[str]:
    return {email.strip().lower() for email in settings.ADMIN_EMAILS.split(",") if email.strip()}


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email.lower() not in _admin_emails():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def _initials_from_email(email: str) -> str:
    local_part = email.split("@", 1)[0]
    tokens = [token for token in local_part.replace(".", " ").replace("_", " ").replace("-", " ").split() if token]

    if len(tokens) >= 2:
        return f"{tokens[0][0]}{tokens[1][0]}".upper()
    if len(local_part) >= 2:
        return local_part[:2].upper()
    return (local_part[:1] or "IT").upper().ljust(2, "T")


def _recent_joiners(db: Session) -> list[str]:
    recent_entries = (
        db.query(WaitlistEntry)
        .order_by(WaitlistEntry.created_at.desc())
        .limit(5)
        .all()
    )
    return [_initials_from_email(entry.email) for entry in reversed(recent_entries)]


def _stats_payload(db: Session) -> dict[str, int | list[str]]:
    total_joined = db.query(WaitlistEntry).count()
    total_seats = settings.WAITLIST_TOTAL_SEATS
    return {
        "total_joined": total_joined,
        "total_seats": total_seats,
        "remaining_seats": max(total_seats - total_joined, 0),
        "recent_joiners": _recent_joiners(db),
    }


@router.get("", response_model=WaitlistStatsResponse)
async def get_waitlist_stats(db: Session = Depends(get_db)):
    return _stats_payload(db)


@router.get("/me", response_model=WaitlistMemberStatusResponse)
async def get_my_waitlist_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == current_user.email.lower()).first()
    position = None
    if entry is not None:
        position = db.query(WaitlistEntry).filter(WaitlistEntry.created_at <= entry.created_at).count()

    return {
        "email": current_user.email,
        "joined": entry is not None,
        "access_approved": bool(entry.access_approved) if entry is not None else False,
        "approved_at": entry.approved_at if entry is not None else None,
        "position": position,
        **_stats_payload(db),
    }


@router.post("", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    payload: WaitlistRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    existing = db.query(WaitlistEntry).filter(WaitlistEntry.email == normalized_email).first()

    if existing:
        response.status_code = status.HTTP_200_OK
        position = db.query(WaitlistEntry).filter(WaitlistEntry.created_at <= existing.created_at).count()
        return {
            "message": "You're already on the waitlist!",
            "position": position,
            "already_joined": True,
            **_stats_payload(db),
        }

    entry = WaitlistEntry(
        email=normalized_email,
        name=payload.name.strip() if payload.name else None,
        profession=payload.profession.strip() if payload.profession else None,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    position = db.query(WaitlistEntry).count()
    background_tasks.add_task(send_waitlist_confirmation_email, normalized_email, position, entry.name)

    return {
        "message": "You're on the list!",
        "position": position,
        "already_joined": False,
        **_stats_payload(db),
    }


@router.get("/admin/entries", response_model=WaitlistAdminEntriesResponse)
async def list_waitlist_entries(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    entries = db.query(WaitlistEntry).order_by(WaitlistEntry.created_at.desc()).all()
    return {
        "entries": [
            WaitlistAdminEntryResponse.model_validate(entry)
            for entry in entries
        ]
    }


@router.post("/admin/approve")
async def approve_waitlist_user(
    payload: WaitlistAdminActionRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == normalized_email).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found")

    entry.access_approved = True
    entry.approved_at = utc_now()
    entry.approved_by = admin.email.lower()
    db.commit()
    return {"message": "Access approved", "email": normalized_email}


@router.post("/admin/revoke")
async def revoke_waitlist_user(
    payload: WaitlistAdminActionRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    normalized_email = payload.email.strip().lower()
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.email == normalized_email).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found")

    entry.access_approved = False
    entry.approved_at = None
    entry.approved_by = None
    db.commit()
    return {"message": "Access revoked", "email": normalized_email}
