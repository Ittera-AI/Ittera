"""
SocialService — manages social platform OAuth connections and LinkedIn credentials.

Responsibilities:
  - Build OAuth URLs for LinkedIn (posting) and Google Drive (storage)
  - Handle Google Drive OAuth callback: exchange code, create Drive folders, upsert connection
  - Store LinkedIn credentials encrypted for the scraper
  - Store OAuth tokens encrypted for security
  - Return connection status for all platforms
"""

import logging
import secrets
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decrypt_value, encrypt_value
from app.models.social_connection import SocialConnection
from app.schemas.social import PlatformStatus, SocialStatusResponse
from app.services.storage_service import StorageService

logger = logging.getLogger("iterra.social")


# ── LinkedIn OAuth URL (for publishing / posting) ───────────────────────────

def build_linkedin_oauth_url() -> str:
    """
    Returns LinkedIn OAuth authorization URL.
    Scopes: openid profile email w_member_social r_member_social
    """
    query = urlencode({
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "scope": "openid profile email w_member_social r_member_social",
        "state": _make_state(),
    })
    return f"https://www.linkedin.com/oauth/v2/authorization?{query}"


# ── Google Drive OAuth ───────────────────────────────────────────────────────

def build_google_drive_oauth_url(user_id: str) -> str:
    """
    Returns Google OAuth URL scoped to drive.file only (not the user's full Drive).
    user_id is passed as state so the callback can identify which user to associate.
    """
    query = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_DRIVE_REDIRECT_URI,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": user_id,
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


async def handle_google_drive_callback(
    db: Session,
    code: str,
    user_id: str,
) -> SocialConnection:
    """
    Exchanges the authorization code for Drive tokens.
    Creates Iterra/ folder structure in the user's Drive.
    Upserts a SocialConnection record with encrypted tokens and folder IDs stored in metadata.
    """
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
    expires_in: int = tokens.get("expires_in", 3600)
    if not access_token:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Google did not return an access token",
        )

    # Create Iterra folder structure in user's Drive (using plaintext tokens temporarily)
    storage = StorageService(access_token=access_token, refresh_token=refresh_token)
    folder_ids = storage.setup_iterra_folder()

    # Encrypt tokens before storing in database
    encrypted_access_token = encrypt_value(access_token)
    encrypted_refresh_token = encrypt_value(refresh_token) if refresh_token else None

    # Calculate token expiry time
    from datetime import datetime, timezone, timedelta
    token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    conn = _upsert_connection(
        db,
        user_id=user_id,
        platform="google_drive",
        platform_user_id=user_id,
        access_token=encrypted_access_token,
        refresh_token=encrypted_refresh_token,
        token_expires_at=token_expires_at,
        scopes=["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/calendar.events"],
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
        client.get_profile(urn_id=None)
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

# Required scopes for Google Drive integration
REQUIRED_DRIVE_SCOPES = {"https://www.googleapis.com/auth/drive.file"}


def get_drive_connection(db: Session, user_id: str) -> Optional[SocialConnection]:
    """
    Returns the active Google Drive SocialConnection or None.
    Validates that the connection has required scopes.
    """
    conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform="google_drive", is_active=True)
        .first()
    )

    if not conn:
        return None

    # Validate scopes
    if not _validate_drive_scopes(conn.scopes):
        logger.warning(
            "User %s Google Drive connection missing required scopes: %s",
            user_id,
            conn.scopes,
        )
        return None

    return conn


REQUIRED_CALENDAR_SCOPES = {"https://www.googleapis.com/auth/calendar.events"}

def get_calendar_connection(db: Session, user_id: str) -> Optional[SocialConnection]:
    """
    Returns the active Google Connection that has calendar scopes or None.
    """
    conn = (
        db.query(SocialConnection)
        .filter_by(user_id=user_id, platform="google_drive", is_active=True)
        .first()
    )
    if not conn or not conn.scopes:
        return None
        
    scope_set = set(conn.scopes)
    if not REQUIRED_CALENDAR_SCOPES.issubset(scope_set):
        return None
        
    return conn


def _validate_drive_scopes(scopes: Optional[list[str]]) -> bool:
    """
    Validate that the stored scopes include all required Drive scopes.

    Args:
        scopes: List of OAuth scopes stored for the connection

    Returns:
        True if all required scopes are present, False otherwise
    """
    if not scopes:
        return False

    scope_set = set(scopes)
    return REQUIRED_DRIVE_SCOPES.issubset(scope_set)


def check_drive_scope_status(conn: Optional[SocialConnection]) -> dict:
    """
    Check the scope status of a Google Drive connection.

    Returns:
        Dict with 'valid' (bool), 'missing_scopes' (list), and 'current_scopes' (list)
    """
    if not conn:
        return {
            "valid": False,
            "missing_scopes": list(REQUIRED_DRIVE_SCOPES),
            "current_scopes": [],
            "message": "No Google Drive connection found",
        }

    current_scopes = set(conn.scopes or [])
    missing = REQUIRED_DRIVE_SCOPES - current_scopes

    return {
        "valid": len(missing) == 0,
        "missing_scopes": list(missing),
        "current_scopes": list(current_scopes),
        "message": "Scopes valid" if not missing else f"Missing scopes: {list(missing)}",
    }


# ── Internal helpers ─────────────────────────────────────────────────────────

def _upsert_connection(
    db: Session,
    user_id: str,
    platform: str,
    platform_user_id: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    token_expires_at: Optional[datetime] = None,
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
    conn.access_token = access_token
    conn.refresh_token = refresh_token or conn.refresh_token
    conn.token_expires_at = token_expires_at
    conn.scopes = scopes or conn.scopes or []
    conn.connection_metadata = metadata or conn.connection_metadata or {}
    conn.is_active = True
    db.commit()
    db.refresh(conn)
    return conn


def _make_state() -> str:
    return secrets.token_urlsafe(16)
