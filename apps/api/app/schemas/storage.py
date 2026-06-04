from typing import Optional

from pydantic import BaseModel


class StorageStatus(BaseModel):
    connected: bool
    iterra_folder_id: Optional[str] = None
    drafts_folder_id: Optional[str] = None
    scraped_posts_file_id: Optional[str] = None
    brand_analysis_file_id: Optional[str] = None


class StorageFileInfo(BaseModel):
    id: str
    name: str
    mime_type: Optional[str] = None
    size: Optional[str] = None
    modified_at: Optional[str] = None


class StorageExportResponse(BaseModel):
    files: list[StorageFileInfo]
    total: int
    message: str = "Files listed from your Google Drive. Download them directly from Drive."


class DeleteDataResponse(BaseModel):
    deleted_files: int
    db_records_cleared: bool
    message: str


class StorageHealthResponse(BaseModel):
    healthy: bool
    connected: bool
    can_read: bool
    can_write: bool
    scopes_valid: bool
    message: str
    last_checked: Optional[str] = None


class DataExportDownloadResponse(BaseModel):
    """Response for downloading all user data (GDPR Article 20 - data portability)."""

    export_data: dict
    export_timestamp: str
    total_files: int
    total_drafts: int
    message: str = "Data export generated successfully. This includes all data stored in your Google Drive."


class DataImportResponse(BaseModel):
    """Response for importing user data."""

    success: bool
    scraped_posts_imported: bool
    brand_analysis_imported: bool
    drafts_imported: int
    drafts_skipped: int
    errors: list[str]
    import_timestamp: str
    message: str


class DataLocationInfo(BaseModel):
    """Information about where a specific data type is stored."""

    data_type: str
    storage_location: str  # "google_drive", "iterra_db", "both", "none"
    description: str
    drive_file_id: Optional[str] = None
    last_updated: Optional[str] = None
    size_approximate: Optional[str] = None  # Human-readable size


class PrivacyDashboardResponse(BaseModel):
    """Privacy dashboard showing where user data is stored."""

    user_id: str
    generated_at: str

    # Data locations
    data_locations: list[DataLocationInfo]

    # Connection status
    drive_connected: bool
    drive_folder_id: Optional[str] = None

    # Storage preferences
    storage_preferences: dict

    # Retention policy
    data_retention_days: Optional[int]
    next_cleanup_date: Optional[str]

    # Audit summary
    recent_exports: list[dict]  # Last 5 exports
    last_accessed: Optional[str]  # Last time data was accessed

    # Queue status (for offline operations)
    pending_operations: int

    # Privacy controls
    can_export: bool
    can_delete: bool

    message: str = "Privacy dashboard - see where your data lives"
