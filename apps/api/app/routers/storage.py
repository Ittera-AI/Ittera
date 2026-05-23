"""
Storage router — Google Drive connection status, export, and GDPR deletion.
Routes: /api/v1/storage/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_workspace_user
from app.dependencies.db import get_db
from app.models.brand_profile import BrandProfile
from app.models.content_draft import ContentDraft
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.schemas.storage import DeleteDataResponse, StorageExportResponse, StorageFileInfo, StorageStatus
from app.services.social_service import decrypt_stored_secret, get_drive_connection
from app.services.storage_service import StorageError, StorageService

router = APIRouter()


@router.get("/status", response_model=StorageStatus)
async def storage_status(
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    conn = get_drive_connection(db, str(current_user.id))
    if not conn:
        return StorageStatus(connected=False)

    meta = conn.connection_metadata or {}

    # Get brand analysis file ID from brand profile
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == current_user.id).first()

    # Get scraped posts file ID from linkedin connection metadata
    linkedin_conn = (
        db.query(SocialConnection)
        .filter_by(user_id=current_user.id, platform="linkedin", is_active=True)
        .first()
    )
    posts_file_id = (
        (linkedin_conn.connection_metadata or {}).get("drive_posts_file_id")
        if linkedin_conn
        else None
    )

    return StorageStatus(
        connected=True,
        iterra_folder_id=meta.get("iterra_folder_id"),
        drafts_folder_id=meta.get("drafts_folder_id"),
        scraped_posts_file_id=posts_file_id,
        brand_analysis_file_id=profile.drive_analysis_file_id if profile else None,
    )


@router.get("/export", response_model=StorageExportResponse)
async def export_data(
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    """Lists all Iterra files in user's Drive. Files are in Drive — user downloads directly."""
    conn = get_drive_connection(db, str(current_user.id))
    if not conn:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect Google Drive first")

    meta = conn.connection_metadata or {}
    folder_id = meta.get("iterra_folder_id")
    if not folder_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Iterra folder not found in Drive")

    storage = StorageService(
        decrypt_stored_secret(conn.access_token) or "",
        decrypt_stored_secret(conn.refresh_token),
    )
    try:
        files = storage.list_all_iterra_files(folder_id)
    except StorageError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))

    items = [
        StorageFileInfo(
            id=f["id"],
            name=f["name"],
            mime_type=f.get("mimeType"),
            size=f.get("size"),
            modified_at=f.get("modifiedTime"),
        )
        for f in files
    ]
    return StorageExportResponse(files=items, total=len(items))


@router.delete("/data", response_model=DeleteDataResponse)
async def delete_all_data(
    current_user: User = Depends(get_current_workspace_user),
    db: Session = Depends(get_db),
):
    """
    GDPR: Deletes all Iterra-created files from user's Drive.
    Clears drive_file_id and drive_analysis_file_id from our DB.
    Does NOT delete the user account or non-Iterra Drive files.
    """
    conn = get_drive_connection(db, str(current_user.id))
    deleted = 0

    if conn:
        meta = conn.connection_metadata or {}
        folder_id = meta.get("iterra_folder_id")
        if folder_id:
            storage = StorageService(
                decrypt_stored_secret(conn.access_token) or "",
                decrypt_stored_secret(conn.refresh_token),
            )
            files = storage.list_all_iterra_files(folder_id)
            for f in files:
                try:
                    storage.delete_file(f["id"])
                    deleted += 1
                except StorageError:
                    pass
            try:
                storage.delete_file(folder_id)
            except StorageError:
                pass

        conn.is_active = False
        conn.connection_metadata = {}

    # Clear Drive references from DB (no content in our DB — just file IDs)
    db.query(ContentDraft).filter(ContentDraft.user_id == current_user.id).update(
        {"drive_file_id": None}
    )
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == current_user.id).first()
    if profile:
        profile.drive_analysis_file_id = None
    db.commit()

    return DeleteDataResponse(
        deleted_files=deleted,
        db_records_cleared=True,
        message=(
            "All Iterra files deleted from your Drive. "
            "Your account data (profile, settings) remains intact."
        ),
    )
