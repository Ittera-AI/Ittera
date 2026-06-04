"""
Celery task: process_storage_queue

Background task for processing queued storage operations when Drive is unavailable.

Features:
  - Processes pending storage operations from Redis queue
  - Retry with exponential backoff
  - Dead letter queue for permanently failed operations
  - Health check before processing
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from workers.celery.app import celery_app

logger = logging.getLogger(__name__)


def _resolve_api_root() -> Path:
    """Locate apps/api whether the worker runs from repo root or /app in Docker."""
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "apps" / "api"
        if candidate.is_dir() and (candidate / "main.py").is_file():
            return candidate
    raise RuntimeError("Could not resolve apps/api from storage_sync task path")


@celery_app.task(
    name="workers.celery.tasks.storage_sync.process_storage_queue",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute between retries
    time_limit=300,  # 5 minute hard limit
    soft_time_limit=240,  # 4 minute soft limit
)
def process_storage_queue(self, user_id: str | None = None, max_operations: int = 50) -> dict:
    """
    Process pending storage operations from the queue.

    This task runs periodically to retry Drive operations that failed
    due to temporary issues (network, rate limits, etc.).

    Args:
        user_id: Optional user ID to process only their operations
        max_operations: Maximum number of operations to process per run

    Returns:
        Dict with processing results
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.config import settings
    from app.services.storage_queue import StorageQueueService, StorageOperationType
    from app.services.storage_service import StorageService, StorageError
    from app.services.social_service import get_drive_connection
    from app.models.content_draft import ContentDraft

    logger.info("Starting storage queue processing (user_id=%s)", user_id or "all")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    queue = StorageQueueService()
    results = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }

    try:
        # Check if queue is available
        if not queue.is_available():
            logger.warning("Storage queue not available (Redis disconnected)")
            return {**results, "error": "Queue not available"}

        # Get pending operations
        operations = queue.get_pending_operations(user_id=user_id, limit=max_operations)

        if not operations:
            logger.debug("No pending storage operations")
            return results

        logger.info("Found %d pending storage operations", len(operations))

        # Group operations by user for efficiency
        ops_by_user = {}
        for op in operations:
            uid = op.get("user_id")
            ops_by_user.setdefault(uid, []).append(op)

        # Process each user's operations
        for uid, user_ops in ops_by_user.items():
            try:
                # Get user's Drive connection
                conn = get_drive_connection(db, uid)
                if not conn:
                    logger.warning("User %s has no Drive connection, skipping %d ops", uid, len(user_ops))
                    results["skipped"] += len(user_ops)
                    # Mark all as failed (will retry later)
                    for op in user_ops:
                        queue.update_operation_status(
                            op["id"],
                            "pending",  # Keep pending, will retry later
                            error="No Drive connection available",
                        )
                    continue

                # Initialize StorageService
                storage = StorageService(
                    access_token=conn.access_token,
                    refresh_token=conn.refresh_token,
                    encrypted=True,
                    expires_at=conn.token_expires_at,
                )

                # Test health before processing
                health = storage.health_check()
                if not health["healthy"]:
                    logger.warning(
                        "Drive health check failed for user %s: %s",
                        uid,
                        health["message"],
                    )
                    results["skipped"] += len(user_ops)
                    # Keep pending, will retry later
                    for op in user_ops:
                        queue.update_operation_status(
                            op["id"],
                            "pending",
                            error=f"Drive health check failed: {health['message']}",
                        )
                    continue

                # Process each operation
                for op in user_ops:
                    try:
                        results["processed"] += 1

                        # Update status to processing
                        queue.update_operation_status(op["id"], "processing")

                        # Execute the operation
                        success = _execute_operation(
                            db=db,
                            storage=storage,
                            operation=op,
                            conn=conn,
                        )

                        if success:
                            queue.update_operation_status(op["id"], "completed")
                            results["succeeded"] += 1
                            logger.debug("Completed operation %s", op["id"])
                        else:
                            # Check retry count
                            retry_count = op.get("retry_count", 0)
                            if retry_count >= queue.MAX_RETRIES:
                                queue.update_operation_status(
                                    op["id"],
                                    "failed",
                                    error="Max retries exceeded",
                                )
                                results["failed"] += 1
                            else:
                                queue.update_operation_status(
                                    op["id"],
                                    "pending",
                                    error="Operation failed, will retry",
                                )
                                results["skipped"] += 1

                    except Exception as e:
                        logger.exception("Failed to process operation %s: %s", op["id"], e)
                        results["errors"].append(f"{op['id']}: {str(e)}")

                        # Check retry count
                        retry_count = op.get("retry_count", 0) + 1
                        if retry_count >= queue.MAX_RETRIES:
                            queue.update_operation_status(op["id"], "failed", error=str(e))
                            results["failed"] += 1
                        else:
                            queue.update_operation_status(
                                op["id"], "pending", error=f"Retry {retry_count}: {str(e)}"
                            )

                # Commit any DB changes
                db.commit()

            except Exception as e:
                logger.exception("Failed to process user %s operations: %s", uid, e)
                results["errors"].append(f"user_{uid}: {str(e)}")
                db.rollback()

        logger.info(
            "Storage queue processing complete: %d processed, %d succeeded, %d failed, %d skipped",
            results["processed"],
            results["succeeded"],
            results["failed"],
            results["skipped"],
        )

        return results

    except Exception as e:
        db.rollback()
        logger.exception("Storage queue processing failed: %s", e)
        raise self.retry(exc=e, countdown=300)

    finally:
        db.close()


def _execute_operation(
    db,
    storage: StorageService,
    operation: dict,
    conn: Any,
) -> bool:
    """
    Execute a single storage operation.

    Args:
        db: Database session
        storage: StorageService instance
        operation: Operation dict from queue
        conn: SocialConnection for the user

    Returns:
        True if successful, False otherwise
    """
    from app.models.content_draft import ContentDraft
    from app.services.storage_queue import StorageOperationType

    op_type = operation.get("operation_type")
    data = operation.get("data", {})
    draft_id = operation.get("draft_id")

    try:
        if op_type == StorageOperationType.SAVE_DRAFT.value:
            # Get folder IDs from connection metadata
            meta = conn.connection_metadata or {}
            drafts_folder_id = meta.get("drafts_folder_id")
            if not drafts_folder_id:
                logger.error("No drafts folder ID for user %s", conn.user_id)
                return False

            # Save draft to Drive
            file_id = storage.save_draft(
                drafts_folder_id=drafts_folder_id,
                draft_id=draft_id or data.get("draft_id"),
                draft_data=data,
            )

            # Update draft with file ID
            if draft_id:
                draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id).first()
                if draft:
                    draft.drive_file_id = file_id

            return True

        elif op_type == StorageOperationType.UPDATE_DRAFT.value:
            file_id = data.get("drive_file_id")
            if not file_id:
                logger.error("No drive_file_id for update operation")
                return False

            storage.update_draft(file_id=file_id, draft_data=data)
            return True

        elif op_type == StorageOperationType.DELETE_DRAFT.value:
            file_id = data.get("drive_file_id")
            if file_id:
                storage.delete_file(file_id=file_id)
            return True

        elif op_type == StorageOperationType.SAVE_BRAND_ANALYSIS.value:
            meta = conn.connection_metadata or {}
            folder_id = meta.get("iterra_folder_id")
            if not folder_id:
                logger.error("No Iterra folder ID for user %s", conn.user_id)
                return False

            file_id = storage.save_brand_analysis(
                folder_id=folder_id,
                analysis_data=data,
                existing_file_id=data.get("existing_file_id"),
            )
            return True

        elif op_type == StorageOperationType.SAVE_SCRAPED_POSTS.value:
            meta = conn.connection_metadata or {}
            folder_id = meta.get("iterra_folder_id")
            if not folder_id:
                logger.error("No Iterra folder ID for user %s", conn.user_id)
                return False

            file_id = storage.save_scraped_posts(
                folder_id=folder_id,
                posts_data=data,
                existing_file_id=data.get("existing_file_id"),
            )
            return True

        else:
            logger.warning("Unknown operation type: %s", op_type)
            return False

    except StorageError as e:
        logger.error("Storage error executing operation: %s", e)
        return False
    except Exception as e:
        logger.exception("Unexpected error executing operation: %s", e)
        return False


@celery_app.task(
    name="workers.celery.tasks.storage_sync.cleanup_old_queue_items",
    bind=True,
    max_retries=2,
)
def cleanup_old_queue_items(self, max_age_days: int = 7) -> dict:
    """
    Clean up old completed/failed queue items.

    Args:
        max_age_days: Maximum age of items to keep

    Returns:
        Dict with cleanup results
    """
    api_root = _resolve_api_root()
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from app.services.storage_queue import StorageQueueService

    logger.info("Starting storage queue cleanup (max_age=%d days)", max_age_days)

    queue = StorageQueueService()

    if not queue.is_available():
        return {"cleaned": 0, "error": "Queue not available"}

    try:
        # Get stats before cleanup
        stats = queue.get_queue_stats()

        # Clean old items from completed and failed lists
        # This is handled by Redis list trimming (LTRIM) in the normal flow,
        # but we can add additional cleanup here if needed

        return {
            "cleaned": 0,  # Placeholder - actual cleanup done via LTRIM
            "stats": stats,
        }

    except Exception as e:
        logger.exception("Queue cleanup failed: %s", e)
        raise self.retry(exc=e, countdown=300)
