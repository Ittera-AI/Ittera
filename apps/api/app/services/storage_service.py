"""
StorageService — wraps all Google Drive operations for Iterra.

Privacy-first design:
  - All content data (posts, analysis, drafts) lives in the user's Google Drive
  - Our DB stores only file IDs and metadata needed to route requests
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

import io
import json
import logging
from typing import Any, Optional

from fastapi import Response
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials

from app.config import settings

logger = logging.getLogger("iterra.storage")


class StorageError(Exception):
    """Raised when a Drive API operation fails."""


class StorageService:
    ITERRA_FOLDER_NAME = "Iterra"
    DRAFTS_FOLDER_NAME = "drafts"

    def __init__(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        self._credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
        )
        self._drive = build("drive", "v3", credentials=self._credentials)

    def _ensure_fresh_credentials(self) -> None:
        """Refresh access token when expired (Drive returns 401 without this)."""
        if not self._credentials.refresh_token:
            return
        if not self._credentials.expired:
            return
        from google.auth.transport.requests import Request

        try:
            self._credentials.refresh(Request())
        except Exception as exc:
            logger.warning("Google Drive token refresh failed: %s", exc)
            raise StorageError(
                "Google Drive session expired. Reconnect Google Drive in Settings."
            ) from exc

    # ── Folder setup ─────────────────────────────────────────────────────────

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

    def write_json(
        self,
        folder_id: str,
        filename: str,
        data: Any,
        existing_file_id: Optional[str] = None,
    ) -> dict:
        """
        Writes or overwrites a JSON file in the specified Drive folder.
        If existing_file_id is given, updates that file in-place (no duplicate).
        Returns file metadata dict with at least {"id": str}.
        """
        try:
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
            else:
                meta = {"name": filename, "parents": [folder_id]}
                file = (
                    self._drive.files()
                    .create(
                        body=meta, media_body=media, fields="id,name,size,modifiedTime"
                    )
                    .execute()
                )

            logger.info(
                "Wrote %s → Drive file %s (%s bytes)",
                filename,
                file["id"],
                file.get("size", "?"),
            )
            return file

        except Exception as exc:
            raise StorageError(
                f"Failed to write {filename} to Drive: {exc}"
            ) from exc

    def read_json(self, file_id: str) -> Any:
        """
        Downloads and parses a JSON file by Drive file ID.
        Raises StorageError if the file cannot be read.
        """
        try:
            self._ensure_fresh_credentials()
            request = self._drive.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)
            return json.loads(buf.read().decode("utf-8"))
        except Exception as exc:
            raise StorageError(
                f"Failed to read file {file_id} from Drive: {exc}"
            ) from exc

    def file_exists(self, file_id: str) -> bool:
        try:
            self._ensure_fresh_credentials()
            self._drive.files().get(fileId=file_id, fields="id").execute()
            return True
        except Exception:
            return False

    def delete_file(self, file_id: str) -> None:
        try:
            self._ensure_fresh_credentials()
            self._drive.files().delete(fileId=file_id).execute()
        except Exception as exc:
            raise StorageError(f"Failed to delete file {file_id}: {exc}") from exc

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
