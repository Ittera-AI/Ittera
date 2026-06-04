"""
Storage router — Google Drive connection status, export, health check, and GDPR deletion.
Routes: /api/v1/storage/*
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.brand_profile import BrandProfile
from app.models.content_draft import ContentDraft
from app.models.social_connection import SocialConnection
from app.models.user import User
from app.schemas.storage import (
    DataExportDownloadResponse,
    DataImportResponse,
    DataLocationInfo,
    DeleteDataResponse,
    PrivacyDashboardResponse,
    StorageExportResponse,
    StorageFileInfo,
    StorageHealthResponse,
    StorageStatus,
)
from app.services.social_service import check_drive_scope_status, get_drive_connection
from app.services.storage_service import StorageError, StorageService

router = APIRouter()


@router.get("/status", response_model=StorageStatus)
async def storage_status(
    current_user: User = Depends(get_current_user),
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


@router.get("/health", response_model=StorageHealthResponse)
async def storage_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check the health of the Google Drive connection.
    Tests connectivity, permissions, and token validity.
    """
    conn = get_drive_connection(db, str(current_user.id))

    if not conn:
        return StorageHealthResponse(
            healthy=False,
            connected=False,
            can_read=False,
            can_write=False,
            scopes_valid=False,
            message="Google Drive not connected",
        )

    # Check scope status
    scope_status = check_drive_scope_status(conn)

    # Perform actual health check via StorageService
    storage = StorageService(
        conn.access_token,
        conn.refresh_token,
        encrypted=True,
        expires_at=conn.token_expires_at,
    )

    try:
        health = storage.health_check()
        return StorageHealthResponse(
            healthy=health["healthy"],
            connected=True,
            can_read=health["can_read"],
            can_write=health["can_write"],
            scopes_valid=scope_status["valid"],
            message=health["message"],
            last_checked=datetime.now(timezone.utc).isoformat(),
        )
    except StorageError as exc:
        return StorageHealthResponse(
            healthy=False,
            connected=True,
            can_read=False,
            can_write=False,
            scopes_valid=scope_status["valid"],
            message=str(exc),
            last_checked=datetime.now(timezone.utc).isoformat(),
        )


@router.get("/export", response_model=StorageExportResponse)
async def export_data(
    current_user: User = Depends(get_current_user),
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
        conn.access_token,
        conn.refresh_token,
        encrypted=True,
        expires_at=conn.token_expires_at,
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
    current_user: User = Depends(get_current_user),
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
                conn.access_token,
                conn.refresh_token,
                encrypted=True,
                expires_at=conn.token_expires_at,
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


@router.get("/export/download", response_model=DataExportDownloadResponse)
async def export_all_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export all Iterra data from user's Google Drive (GDPR Article 20).

    Returns a complete export of:
    - Scraped posts data
    - Brand analysis data
    - Content drafts
    - File metadata

    This enables data portability - users can take their data elsewhere.
    """
    conn = get_drive_connection(db, str(current_user.id))
    if not conn:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect Google Drive first")

    meta = conn.connection_metadata or {}
    folder_id = meta.get("iterra_folder_id")
    drafts_folder_id = meta.get("drafts_folder_id")

    if not folder_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Iterra folder not found in Drive")

    storage = StorageService(
        conn.access_token,
        conn.refresh_token,
        encrypted=True,
        expires_at=conn.token_expires_at,
    )

    try:
        export_data = storage.export_all_data(folder_id, drafts_folder_id, user_id=str(current_user.id))

        return DataExportDownloadResponse(
            export_data=export_data,
            export_timestamp=datetime.now(timezone.utc).isoformat(),
            total_files=len(export_data.get("files", [])),
            total_drafts=len(export_data.get("drafts", [])),
        )

    except StorageError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@router.post("/import", response_model=DataImportResponse)
async def import_data(
    data: dict,
    overwrite: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import Iterra data to user's Google Drive.

    Restores data from a previous export (from export/download).
    Use with caution - validates data format before import.

    Args:
        data: The export data to import
        overwrite: If True, overwrite existing files; if False, skip existing
    """
    conn = get_drive_connection(db, str(current_user.id))
    if not conn:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect Google Drive first")

    meta = conn.connection_metadata or {}
    folder_id = meta.get("iterra_folder_id")
    drafts_folder_id = meta.get("drafts_folder_id")

    if not folder_id or not drafts_folder_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Iterra folder structure incomplete. Please reconnect Google Drive."
        )

    # Validate import data format
    if not data.get("export_metadata"):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Invalid export format: missing export_metadata"
        )

    storage = StorageService(
        conn.access_token,
        conn.refresh_token,
        encrypted=True,
        expires_at=conn.token_expires_at,
    )

    try:
        results = storage.import_data(
            folder_id=folder_id,
            drafts_folder_id=drafts_folder_id,
            data=data,
            overwrite=overwrite,
            user_id=str(current_user.id),
        )

        return DataImportResponse(
            success=len(results.get("errors", [])) == 0,
            scraped_posts_imported=results["scraped_posts"],
            brand_analysis_imported=results["brand_analysis"],
            drafts_imported=results["drafts_imported"],
            drafts_skipped=results["drafts_skipped"],
            errors=results["errors"],
            import_timestamp=results["imported_at"],
            message=(
                f"Import completed. {results['drafts_imported']} drafts imported, "
                f"{results['drafts_skipped']} skipped. "
                f"{len(results['errors'])} errors."
            ),
        )

    except StorageError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))


@router.get("/privacy-dashboard", response_model=PrivacyDashboardResponse)
async def privacy_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Privacy dashboard showing where user data is stored.

    Provides transparency about:
    - Which data types are stored where (Drive vs Iterra)
    - Storage preferences
    - Data retention policy
    - Pending operations
    - Recent access history
    """
    conn = get_drive_connection(db, str(current_user.id))
    drive_connected = conn is not None

    # Build data locations list
    data_locations: list[DataLocationInfo] = []

    # Check drafts location
    drafts_count = db.query(ContentDraft).filter(
        ContentDraft.user_id == current_user.id
    ).count()
    drafts_in_drive = db.query(ContentDraft).filter(
        ContentDraft.user_id == current_user.id,
        ContentDraft.drive_file_id.isnot(None)
    ).count()

    if drafts_in_drive > 0 and drafts_in_drive == drafts_count:
        draft_location = "google_drive"
    elif drafts_in_drive > 0:
        draft_location = "both"
    elif drafts_count > 0:
        draft_location = "iterra_db"
    else:
        draft_location = "none"

    data_locations.append(DataLocationInfo(
        data_type="drafts",
        storage_location=draft_location,
        description="Content drafts you create",
        last_updated=datetime.now(timezone.utc).isoformat() if drafts_count > 0 else None,
    ))

    # Check brand analysis location
    profile = db.query(BrandProfile).filter(
        BrandProfile.user_id == current_user.id
    ).first()
    analysis_location = "google_drive" if (profile and profile.drive_analysis_file_id) else "iterra_db" if profile else "none"
    data_locations.append(DataLocationInfo(
        data_type="brand_analysis",
        storage_location=analysis_location,
        description="AI-generated brand profile analysis",
        drive_file_id=profile.drive_analysis_file_id if profile else None,
    ))

    # Check scraped posts location
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
    scraped_location = "google_drive" if posts_file_id else "iterra_db" if linkedin_conn else "none"
    data_locations.append(DataLocationInfo(
        data_type="scraped_posts",
        storage_location=scraped_location,
        description="Posts scraped from your LinkedIn profile",
        drive_file_id=posts_file_id,
    ))

    # Get storage queue status
    from app.services.storage_queue import get_storage_queue
    queue = get_storage_queue()
    queue_stats = queue.get_user_queue_stats(str(current_user.id)) if queue.is_available() else {"pending_count": 0}

    # Get retention policy info
    from app.services.data_retention import DataRetentionService
    retention_service = DataRetentionService(db)
    retention_summary = retention_service.get_retention_summary(current_user)

    return PrivacyDashboardResponse(
        user_id=str(current_user.id),
        generated_at=datetime.now(timezone.utc).isoformat(),
        data_locations=data_locations,
        drive_connected=drive_connected,
        drive_folder_id=conn.connection_metadata.get("iterra_folder_id") if conn else None,
        storage_preferences=current_user.storage_preferences or {"default": "google_drive"},
        data_retention_days=current_user.data_retention_days,
        next_cleanup_date=retention_summary.get("next_cleanup_date"),
        recent_exports=[],  # TODO: Implement from audit logs
        last_accessed=None,  # TODO: Implement from audit logs
        pending_operations=queue_stats.get("pending_count", 0),
        can_export=drive_connected,
        can_delete=True,
    )
