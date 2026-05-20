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
