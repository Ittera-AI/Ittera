"""
SocialService — manages social platform OAuth connections and LinkedIn credentials.

Responsibilities:
  - Build OAuth URLs for LinkedIn (posting) and Google Drive (storage)
  - Handle Google Drive OAuth callback: exchange code, create Drive folders, upsert connection
  - Store LinkedIn credentials encrypted for the scraper
  - Return connection status for all platforms
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decrypt_value, encrypt_value
from app.models.social_connection import SocialConnection
from app.schemas.social import PlatformStatus, SocialStatusResponse
from app.services.storage_service import StorageService

_ENCRYPTED_PREFIX = "fernet:"


# ── LinkedIn OAuth URL (for publishing / posting) ───────────────────────────

def build_linkedin_oauth_url() -> str:
    """
    Returns LinkedIn OAuth authorization URL.
    Scopes: openid profile email w_member_social r_basicprofile
    """
    from app.services.auth_service import make_oauth_state

    query = urlencode({
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email w_member_social r_basicprofile",
        "state": make_oauth_state("linkedin_oauth"),
    })
    return f"https://www.linkedin.com/oauth/v2/authorization?{query}"


# ── Google Drive OAuth ───────────────────────────────────────────────────────

def build_google_drive_oauth_url(user_id: str) -> str:
    """
    Returns Google OAuth URL scoped to drive.file only (not the user's full Drive).
    user_id is signed into state so the callback can identify the user safely.
    """
    query = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_DRIVE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.file",
        "access_type": "offline",
        "prompt": "consent",
        "state": _make_oauth_state("google_drive", user_id),
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


async def handle_google_drive_callback(
    db: Session,
    code: str,
    state: str,
) -> SocialConnection:
    """
    Exchanges the authorization code for Drive tokens.
    Creates Iterra/ folder structure in the user's Drive.
    Upserts a SocialConnection record with folder IDs stored in metadata.
    """
    user_id = _verify_oauth_state(state, "google_drive")

    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_DRIVE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.is_error:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "Google Drive token exchange failed",
            )

    tokens = token_resp.json()
    access_token: str = tokens.get("access_token", "")
    refresh_token: Optional[str] = tokens.get("refresh_token")
    if not access_token:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Google did not return an access token",
        )

    # Create Iterra folder structure in user's Drive
    storage = StorageService(access_token=access_token, refresh_token=refresh_token)
    folder_ids = storage.setup_iterra_folder()

    conn = _upsert_connection(
        db,
        user_id=user_id,
        platform="google_drive",
        platform_user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        scopes=["https://www.googleapis.com/auth/drive.file"],
        metadata={
            "iterra_folder_id": folder_ids["iterra_folder_id"],
            "drafts_folder_id": folder_ids["drafts_folder_id"],
        },
    )
    return conn


# ── LinkedIn credential storage (for scraper) ────────────────────────────────

async def store_linkedin_credentials(
    db: Session,
    user_id: str,
    username: str,
    password: str,
) -> SocialConnection:
    """
    Validates LinkedIn credentials via linkedin-api, then stores them encrypted.
    Raises HTTP 400 if credentials are invalid.
    """
    try:
        from linkedin_api import Linkedin  # type: ignore[import]
        client = Linkedin(username, password)
        # Quick validation: fetch own profile summary
        client.get_profile(public_id=username.split("@")[0])
    except Exception as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"LinkedIn credentials are invalid: {exc}",
        )

    conn = _upsert_connection(
        db,
        user_id=user_id,
        platform="linkedin",
        platform_user_id=username,
        platform_username=username,
        access_token="linkedin-cookie-auth",  # placeholder; scraper uses username/password
        metadata={
            "encrypted_username": encrypt_value(username),
            "encrypted_password": encrypt_value(password),
        },
    )
    return conn


# ── Connection status ─────────────────────────────────────────────────────────

def get_connection_status(db: Session, user_id: str) -> SocialStatusResponse:
    """Returns status of all social platform connections for the user."""
    conns = (
        db.query(SocialConnection)
        .filter(SocialConnection.user_id == user_id)
        .all()
    )

    statuses: list[PlatformStatus] = []
    for conn in conns:
        meta = conn.connection_metadata or {}
        summary: dict = {}
        if conn.platform == "google_drive":
            summary = {
                k: v
                for k, v in meta.items()
                if "folder" in k or "file" in k
            }
        elif conn.platform == "linkedin":
            summary = {
                "last_post_count": meta.get("last_post_count", 0),
                "drive_posts_file_id": meta.get("drive_posts_file_id"),
            }

        statuses.append(
            PlatformStatus(
                platform=conn.platform,
                connected=conn.is_active,
                username=conn.platform_username,
                last_synced_at=(
                    conn.last_synced_at.isoformat()
                    if conn.last_synced_at
                    else None
                ),
                metadata_summary=summary,
            )
        )

    return SocialStatusResponse(connections=statuses)


# ── Drive connection helper ───────────────────────────────────────────────────

def get_drive_connection(db: Session, user_id: str) -> Optional[SocialConnection]:
    """Returns the active Google Drive SocialConnection or None."""
    return (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform="google_drive", is_active=True)
        .first()
    )


# ── Internal helpers ─────────────────────────────────────────────────────────

def _upsert_connection(
    db: Session,
    user_id: str,
    platform: str,
    platform_user_id: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    platform_username: Optional[str] = None,
    scopes: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> SocialConnection:
    conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform=platform)
        .first()
    )
    if conn is None:
        conn = SocialConnection(
            id=str(uuid.uuid4()),
            user_id=user_id,
            platform=platform,
        )
        db.add(conn)

    conn.platform_user_id = platform_user_id
    conn.platform_username = platform_username or conn.platform_username
    conn.access_token = encrypt_stored_secret(access_token) or ""
    conn.refresh_token = encrypt_stored_secret(refresh_token) if refresh_token else conn.refresh_token
    conn.scopes = scopes or conn.scopes or []
    conn.connection_metadata = metadata or conn.connection_metadata or {}
    conn.is_active = True
    db.commit()
    db.refresh(conn)
    return conn


def _make_oauth_state(purpose: str, user_id: str) -> str:
    payload = {
        "purpose": purpose,
        "user_id": user_id,
        "nonce": secrets.token_urlsafe(16),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _verify_oauth_state(state: str, purpose: str) -> str:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        ) from exc

    if payload.get("purpose") != purpose or not payload.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )
    return str(payload["user_id"])


def encrypt_stored_secret(value: str | None) -> str | None:
    if not value:
        return value
    if value.startswith(_ENCRYPTED_PREFIX):
        return value
    return f"{_ENCRYPTED_PREFIX}{encrypt_value(value)}"


def decrypt_stored_secret(value: str | None) -> str | None:
    if not value:
        return value
    if not value.startswith(_ENCRYPTED_PREFIX):
        return value
    return decrypt_value(value.removeprefix(_ENCRYPTED_PREFIX))
