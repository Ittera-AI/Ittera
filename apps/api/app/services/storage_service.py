"""
StorageService — wraps all Google Drive operations for Iterra.

Privacy-first design:
  - All content data (posts, analysis, drafts) lives in the user's Google Drive
  - Our DB stores only file IDs and metadata needed to route requests
  - OAuth tokens are encrypted at rest using Fernet symmetric encryption
  - Every public method is typed and logs its operation
  - On Drive API failure, raises StorageError with an actionable message

Drive folder structure created on OAuth connection:
  Iterra/
    scraped_posts.json
    brand_analysis.json
    analytics_history.json
    drafts/
      {draft-uuid}.json
      ...

The user owns all files. Iterra uses scope drive.file — we can only access
files we created. If the user revokes access, we cannot read their data.
"""

from datetime import datetime, timedelta, timezone
import io
import json
import logging
from typing import Any, Optional

from fastapi import Response
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials

from app.config import settings
from app.core.audit_logger import AuditAction, get_audit_logger
from app.core.retry import drive_api_retry
from app.core.security import decrypt_value

logger = logging.getLogger("iterra.storage")
audit = get_audit_logger()

# Required OAuth scope for Google Drive file operations
REQUIRED_DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"


class StorageError(Exception):
    """Raised when a Drive API operation fails."""


class StorageService:
    ITERRA_FOLDER_NAME = "Iterra"
    DRAFTS_FOLDER_NAME = "drafts"

    # Buffer time (in seconds) to refresh tokens before they expire
    TOKEN_EXPIRY_BUFFER = 300  # 5 minutes

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        encrypted: bool = False,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize StorageService with Google Drive tokens.

        Args:
            access_token: Google Drive access token (plaintext or encrypted)
            refresh_token: Google Drive refresh token (plaintext or encrypted, optional)
            encrypted: If True, tokens will be decrypted before use
            expires_at: Optional datetime when the token expires (for proactive refresh)
        """
        # Decrypt tokens if they are encrypted
        if encrypted:
            decrypted_access = decrypt_value(access_token)
            if not decrypted_access:
                raise StorageError("Failed to decrypt access token. The encryption key may have changed.")
            access_token = decrypted_access

            if refresh_token:
                decrypted_refresh = decrypt_value(refresh_token)
                if decrypted_refresh:
                    refresh_token = decrypted_refresh
                else:
                    refresh_token = None

        self._credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        # Set expiry if provided (for proactive refresh calculation)
        if expires_at:
            from google.auth import datetime as google_datetime
            self._credentials.expiry = expires_at

        self._drive = build("drive", "v3", credentials=self._credentials)

    def _ensure_fresh_credentials(self) -> None:
        """
        Refresh access token when expired or about to expire.
        Proactively refreshes tokens TOKEN_EXPIRY_BUFFER seconds before actual expiry.
        """
        if not self._credentials.refresh_token:
            return

        # Check if token is expired or will expire soon (proactive refresh)
        from google.auth import datetime as google_datetime
        now = google_datetime.utcnow()
        buffer = timedelta(seconds=self.TOKEN_EXPIRY_BUFFER)

        # If we have expiry info, check with buffer; otherwise use default expired check
        if self._credentials.expiry:
            needs_refresh = (self._credentials.expiry - buffer) <= now
        else:
            needs_refresh = self._credentials.expired

        if not needs_refresh:
            return

        from google.auth.transport.requests import Request

        try:
            logger.debug("Proactively refreshing Google Drive token (expires at %s)", self._credentials.expiry)
            self._credentials.refresh(Request())
            logger.info("Google Drive token refreshed successfully")
        except Exception as exc:
            logger.warning("Google Drive token refresh failed: %s", exc)
            raise StorageError(
                "Google Drive session expired. Reconnect Google Drive in Settings."
            ) from exc

    # ── Folder setup ─────────────────────────────────────────────────────────

    @drive_api_retry(max_attempts=3)
    def setup_iterra_folder(self) -> dict:
        """
        Creates Iterra/ and Iterra/drafts/ in the user's Drive (idempotent).
        Called once on Google Drive OAuth connection.
        Returns: {"iterra_folder_id": str, "drafts_folder_id": str}
        """
        iterra = self._create_folder_if_not_exists(self.ITERRA_FOLDER_NAME, parent_id=None)
        drafts = self._create_folder_if_not_exists(
            self.DRAFTS_FOLDER_NAME, parent_id=iterra["id"]
        )
        logger.info(
            "Iterra folder setup: iterra=%s drafts=%s", iterra["id"], drafts["id"]
        )
        return {"iterra_folder_id": iterra["id"], "drafts_folder_id": drafts["id"]}

    @drive_api_retry(max_attempts=3)
    def _create_folder_if_not_exists(
        self, name: str, parent_id: Optional[str]
    ) -> dict:
        query = (
            f"name='{name}' and mimeType='application/vnd.google-apps.folder'"
            " and trashed=false"
        )
        if parent_id:
            query += f" and '{parent_id}' in parents"

        self._ensure_fresh_credentials()
        result = (
            self._drive.files()
            .list(q=query, fields="files(id,name)")
            .execute()
        )
        files = result.get("files", [])
        if files:
            return files[0]

        metadata: dict = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        self._ensure_fresh_credentials()
        return self._drive.files().create(body=metadata, fields="id,name").execute()

    # ── Core read / write ────────────────────────────────────────────────────

    @drive_api_retry(max_attempts=3)
    def write_json(
        self,
        folder_id: str,
        filename: str,
        data: Any,
        existing_file_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Writes or overwrites a JSON file in the specified Drive folder.
        If existing_file_id is given, updates that file in-place (no duplicate).
        Returns file metadata dict with at least {"id": str}.
        """
        self._ensure_fresh_credentials()
        content = json.dumps(data, indent=2, default=str).encode("utf-8")
        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype="application/json", resumable=False
        )

        if existing_file_id:
            file = (
                self._drive.files()
                .update(
                    fileId=existing_file_id,
                    media_body=media,
                    fields="id,name,size,modifiedTime",
                )
                .execute()
            )
            operation = "update"
        else:
            meta = {"name": filename, "parents": [folder_id]}
            file = (
                self._drive.files()
                .create(
                    body=meta, media_body=media, fields="id,name,size,modifiedTime"
                )
                .execute()
            )
            operation = "create"

        logger.info(
            "Wrote %s → Drive file %s (%s bytes)",
            filename,
            file["id"],
            file.get("size", "?"),
        )

        # Audit log
        if user_id:
            audit.storage_write(
                user_id=user_id,
                file_id=file["id"],
                file_name=filename,
                operation=operation,
            )

        return file

    @drive_api_retry(max_attempts=3)
    def read_json(self, file_id: str, user_id: Optional[str] = None) -> Any:
        """
        Downloads and parses a JSON file by Drive file ID.
        Raises StorageError if the file cannot be read.
        """
        self._ensure_fresh_credentials()
        request = self._drive.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        data = json.loads(buf.read().decode("utf-8"))

        # Audit log
        if user_id:
            audit.storage_read(
                user_id=user_id,
                file_id=file_id,
                file_name=data.get("filename") if isinstance(data, dict) else None,
            )

        return data

    @drive_api_retry(max_attempts=3)
    def file_exists(self, file_id: str) -> bool:
        self._ensure_fresh_credentials()
        self._drive.files().get(fileId=file_id, fields="id").execute()
        return True

    @drive_api_retry(max_attempts=3)
    def delete_file(self, file_id: str, user_id: Optional[str] = None, file_name: Optional[str] = None) -> None:
        self._ensure_fresh_credentials()
        self._drive.files().delete(fileId=file_id).execute()

        # Audit log
        if user_id:
            audit.storage_delete(
                user_id=user_id,
                file_id=file_id,
                file_name=file_name,
            )

    # ── Draft helpers ─────────────────────────────────────────────────────────

    def save_draft(
        self, drafts_folder_id: str, draft_id: str, draft_data: dict
    ) -> str:
        """Saves a content draft to /drafts/. Returns Drive file ID."""
        file = self.write_json(
            drafts_folder_id, f"{draft_id}.json", draft_data
        )
        return file["id"]

    def load_draft(self, file_id: str) -> dict:
        return self.read_json(file_id)

    def update_draft(self, file_id: str, draft_data: dict) -> None:
        """Updates an existing draft file in-place."""
        self.write_json("", "", draft_data, existing_file_id=file_id)

    def save_media_file(
        self,
        folder_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
        user_id: Optional[str] = None,
    ) -> str:
        """Saves a binary media file to Drive. Returns Drive file ID."""
        self._ensure_fresh_credentials()
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
        meta = {"name": filename, "parents": [folder_id]}
        file = (
            self._drive.files()
            .create(body=meta, media_body=media, fields="id,name,size,modifiedTime")
            .execute()
        )
        if user_id:
            audit.storage_write(
                user_id=user_id,
                file_id=file["id"],
                file_name=filename,
                operation="create",
            )
        return file["id"]

    # ── Post data helpers ─────────────────────────────────────────────────────

    def save_scraped_posts(
        self,
        folder_id: str,
        posts_data: dict,
        existing_file_id: Optional[str] = None,
    ) -> str:
        """Saves scraped posts JSON. Returns Drive file ID."""
        file = self.write_json(
            folder_id,
            "scraped_posts.json",
            posts_data,
            existing_file_id=existing_file_id,
        )
        return file["id"]

    def load_scraped_posts(self, file_id: str) -> list[dict]:
        """Returns the list of post objects from scraped_posts.json."""
        data = self.read_json(file_id)
        return data.get("posts", [])

    # ── Brand analysis helpers ────────────────────────────────────────────────

    def save_brand_analysis(
        self,
        folder_id: str,
        analysis_data: dict,
        existing_file_id: Optional[str] = None,
    ) -> str:
        """Saves full AI brand analysis JSON. Returns Drive file ID."""
        file = self.write_json(
            folder_id,
            "brand_analysis.json",
            analysis_data,
            existing_file_id=existing_file_id,
        )
        return file["id"]

    def load_brand_analysis(self, file_id: str) -> dict:
        return self.read_json(file_id)

    # ── GDPR / export ────────────────────────────────────────────────────────

    # ── Data Portability (GDPR Article 20) ────────────────────────────────────

    @drive_api_retry(max_attempts=3)
    def export_all_data(
        self,
        folder_id: str,
        drafts_folder_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Export all Iterra data from user's Drive for data portability.

        Returns a structured data export containing:
        - scraped_posts.json content
        - brand_analysis.json content
        - All draft files
        - File metadata

        Args:
            folder_id: The Iterra folder ID
            drafts_folder_id: Optional drafts subfolder ID

        Returns:
            Dict with all exported data
        """
        self._ensure_fresh_credentials()

        export_data = {
            "export_metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "source": "iterra_drive_export",
            },
            "scraped_posts": None,
            "brand_analysis": None,
            "drafts": [],
            "files": [],
        }

        # List all files in the Iterra folder
        files = self.list_all_iterra_files(folder_id)
        export_data["files"] = files

        # Read each file's content
        for file_info in files:
            file_id = file_info.get("id")
            name = file_info.get("name", "")
            mime_type = file_info.get("mimeType", "")

            try:
                if name == "scraped_posts.json":
                    export_data["scraped_posts"] = self.read_json(file_id)
                elif name == "brand_analysis.json":
                    export_data["brand_analysis"] = self.read_json(file_id)
                elif mime_type == "application/vnd.google-apps.folder":
                    # This is the drafts folder - read its contents
                    if name == "drafts" and drafts_folder_id is None:
                        drafts_folder_id = file_id
                        draft_files = self.list_all_iterra_files(file_id)
                        for draft_file in draft_files:
                            try:
                                draft_data = self.read_json(draft_file["id"])
                                export_data["drafts"].append(draft_data)
                            except Exception as e:
                                logger.warning(
                                    "Failed to read draft file %s: %s",
                                    draft_file.get("name"),
                                    e,
                                )
                elif name.endswith(".json"):
                    # Generic JSON file - include in export
                    try:
                        file_content = self.read_json(file_id)
                        export_data.setdefault("other_files", {})[name] = file_content
                    except Exception as e:
                        logger.warning("Failed to read file %s: %s", name, e)

            except Exception as e:
                logger.warning("Failed to export file %s: %s", name, e)

        # Audit log
        if user_id:
            audit.storage_export(
                user_id=user_id,
                total_files=len(export_data.get("files", [])),
                total_drafts=len(export_data.get("drafts", [])),
            )

        return export_data

    @drive_api_retry(max_attempts=3)
    def import_data(
        self,
        folder_id: str,
        drafts_folder_id: str,
        data: dict,
        overwrite: bool = False,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Import Iterra data to user's Drive.

        Restores:
        - scraped_posts.json
        - brand_analysis.json
        - Draft files

        Args:
            folder_id: The Iterra folder ID
            drafts_folder_id: The drafts subfolder ID
            data: The data to import (from export_all_data format)
            overwrite: If True, overwrite existing files; if False, skip existing
            user_id: User ID for audit logging

        Returns:
            Dict with import results
        """
        self._ensure_fresh_credentials()

        results = {
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "scraped_posts": False,
            "brand_analysis": False,
            "drafts_imported": 0,
            "drafts_skipped": 0,
            "errors": [],
        }

        # Import scraped posts
        if data.get("scraped_posts"):
            try:
                # Check for existing file
                existing_id = None
                if not overwrite:
                    files = self.list_all_iterra_files(folder_id)
                    for f in files:
                        if f.get("name") == "scraped_posts.json":
                            existing_id = f.get("id")
                            break

                self.write_json(
                    folder_id,
                    "scraped_posts.json",
                    data["scraped_posts"],
                    existing_file_id=existing_id if overwrite else None,
                )
                results["scraped_posts"] = True
            except Exception as e:
                results["errors"].append(f"scraped_posts: {str(e)}")

        # Import brand analysis
        if data.get("brand_analysis"):
            try:
                # Check for existing file
                existing_id = None
                if not overwrite:
                    files = self.list_all_iterra_files(folder_id)
                    for f in files:
                        if f.get("name") == "brand_analysis.json":
                            existing_id = f.get("id")
                            break

                self.write_json(
                    folder_id,
                    "brand_analysis.json",
                    data["brand_analysis"],
                    existing_file_id=existing_id if overwrite else None,
                )
                results["brand_analysis"] = True
            except Exception as e:
                results["errors"].append(f"brand_analysis: {str(e)}")

        # Import drafts
        for draft in data.get("drafts", []):
            draft_id = draft.get("id", f"imported-{datetime.now(timezone.utc).timestamp()}")
            try:
                # Check if draft already exists
                existing_files = self.list_all_iterra_files(drafts_folder_id)
                existing_id = None
                for f in existing_files:
                    if f.get("name") == f"{draft_id}.json":
                        existing_id = f.get("id")
                        if not overwrite:
                            results["drafts_skipped"] += 1
                            continue
                        break

                if overwrite or not existing_id:
                    self.write_json(
                        drafts_folder_id,
                        f"{draft_id}.json",
                        draft,
                        existing_file_id=existing_id,
                    )
                    results["drafts_imported"] += 1

            except Exception as e:
                results["errors"].append(f"draft_{draft_id}: {str(e)}")

        # Import other files
        for name, content in data.get("other_files", {}).items():
            try:
                self.write_json(folder_id, name, content)
            except Exception as e:
                results["errors"].append(f"{name}: {str(e)}")

        # Audit log
        if user_id:
            audit.storage_import(
                user_id=user_id,
                drafts_imported=results["drafts_imported"],
                drafts_skipped=results["drafts_skipped"],
                success=len(results["errors"]) == 0,
            )

        return results

    @drive_api_retry(max_attempts=3)
    def list_all_iterra_files(self, folder_id: str) -> list[dict]:
        """Lists all files directly inside the Iterra/ folder."""
        if not folder_id or not str(folder_id).strip():
            raise StorageError("Missing Iterra folder id — reconnect Google Drive.")
        self._ensure_fresh_credentials()
        results: list[dict] = []
        page_token = None
        while True:
            resp = (
                self._drive.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    fields="nextPageToken, files(id,name,mimeType,size,modifiedTime)",
                    pageToken=page_token,
                )
                .execute()
            )
            results.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return results

    def health_check(self) -> dict:
        """
        Perform a lightweight health check of the Drive connection.

        Returns:
            Dict with health status information including:
            - healthy: bool
            - can_read: bool
            - can_write: bool
            - scopes_valid: bool
            - message: str
        """
        try:
            self._ensure_fresh_credentials()

            # Check if we can read (list files in root)
            try:
                self._drive.files().list(pageSize=1, fields="files(id)").execute()
                can_read = True
            except Exception as e:
                logger.warning("Drive health check read failed: %s", e)
                can_read = False

            # We can't easily test write without creating a file,
            # but if we can read and have the right scope, write should work
            scopes_valid = self._credentials.scopes and REQUIRED_DRIVE_SCOPE in self._credentials.scopes

            healthy = can_read and scopes_valid

            return {
                "healthy": healthy,
                "can_read": can_read,
                "can_write": scopes_valid,  # Assume write works if scope is valid
                "scopes_valid": scopes_valid,
                "message": "Drive connection is healthy" if healthy else "Drive connection issues detected",
            }

        except Exception as e:
            logger.error("Drive health check failed: %s", e)
            return {
                "healthy": False,
                "can_read": False,
                "can_write": False,
                "scopes_valid": False,
                "message": f"Drive health check failed: {str(e)}",
            }


class LocalStorageAdapter:
    """
    Used when user picks storage_preference='local'.
    Returns content data as a downloadable HTTP response.
    Nothing is persisted server-side beyond lightweight DB metadata.
    """

    def export_as_json(self, data: dict, filename: str) -> Response:
        content = json.dumps(data, indent=2, default=str).encode("utf-8")
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
