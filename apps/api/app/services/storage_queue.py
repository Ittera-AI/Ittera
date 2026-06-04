"""
Storage Queue Service — queues Drive operations when Drive is unavailable.

When a Drive operation fails (network issues, rate limits, etc.),
operations can be queued and retried later via a background Celery task.

Uses Redis as the queue backend for durability and retry support.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

import redis

from app.config import settings

logger = logging.getLogger("iterra.storage_queue")


class StorageOperationType(str, Enum):
    """Types of storage operations that can be queued."""

    SAVE_DRAFT = "save_draft"
    UPDATE_DRAFT = "update_draft"
    DELETE_DRAFT = "delete_draft"
    SAVE_BRAND_ANALYSIS = "save_brand_analysis"
    SAVE_SCRAPED_POSTS = "save_scraped_posts"


class StorageQueueService:
    """
    Service for queuing storage operations when Drive is unavailable.

    Operations are stored in Redis with retry counts and timestamps.
    A background Celery task processes the queue periodically.
    """

    # Redis key prefix for storage queue
    QUEUE_KEY_PREFIX = "iterra:storage:queue"
    # Maximum retry attempts for queued operations
    MAX_RETRIES = 5
    # Initial delay in seconds before first retry
    INITIAL_RETRY_DELAY = 60  # 1 minute
    # Exponential backoff multiplier
    BACKOFF_MULTIPLIER = 2

    def __init__(self) -> None:
        self._redis: Optional[redis.Redis] = None
        try:
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            self._redis.ping()
        except Exception as e:
            logger.warning("Failed to connect to Redis for storage queue: %s", e)
            self._redis = None

    def is_available(self) -> bool:
        """Check if the queue service is available (Redis is connected)."""
        if not self._redis:
            return False
        try:
            return self._redis.ping()
        except Exception:
            return False

    def queue_operation(
        self,
        user_id: str,
        operation_type: StorageOperationType,
        data: dict,
        draft_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Queue a storage operation for later processing.

        Args:
            user_id: The user ID for the operation
            operation_type: Type of operation to perform
            data: The data needed for the operation
            draft_id: Optional draft ID associated with the operation

        Returns:
            The queue job ID if queued successfully, None otherwise
        """
        if not self.is_available():
            logger.error("Cannot queue operation: Redis not available")
            return None

        job_id = f"{operation_type.value}:{user_id}:{datetime.now(timezone.utc).timestamp()}"

        job = {
            "id": job_id,
            "user_id": user_id,
            "operation_type": operation_type.value,
            "draft_id": draft_id,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "retry_count": 0,
            "status": "pending",
            "last_error": None,
        }

        try:
            # Add to sorted set with score as timestamp (for FIFO processing)
            queue_key = f"{self.QUEUE_KEY_PREFIX}:pending"
            self._redis.zadd(queue_key, {json.dumps(job): datetime.now(timezone.utc).timestamp()})

            # Also store in hash for easy lookup
            self._redis.hset(f"{self.QUEUE_KEY_PREFIX}:jobs", job_id, json.dumps(job))

            logger.info("Queued storage operation %s for user %s", operation_type.value, user_id)
            return job_id

        except Exception as e:
            logger.error("Failed to queue storage operation: %s", e)
            return None

    def get_pending_operations(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get pending operations from the queue.

        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of operations to return

        Returns:
            List of pending operation jobs
        """
        if not self.is_available():
            return []

        try:
            queue_key = f"{self.QUEUE_KEY_PREFIX}:pending"
            # Get oldest items first (by score)
            items = self._redis.zrange(queue_key, 0, limit - 1, withscores=False)

            operations = []
            for item in items:
                try:
                    job = json.loads(item)
                    if user_id is None or job.get("user_id") == user_id:
                        operations.append(job)
                except json.JSONDecodeError:
                    continue

            return operations

        except Exception as e:
            logger.error("Failed to get pending operations: %s", e)
            return []

    def get_operation(self, job_id: str) -> Optional[dict]:
        """Get a specific operation by ID."""
        if not self.is_available():
            return None

        try:
            data = self._redis.hget(f"{self.QUEUE_KEY_PREFIX}:jobs", job_id)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error("Failed to get operation %s: %s", job_id, e)
            return None

    def update_operation_status(
        self,
        job_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update the status of a queued operation.

        Args:
            job_id: The operation job ID
            status: New status (pending, processing, completed, failed)
            error: Optional error message if failed

        Returns:
            True if updated successfully
        """
        if not self.is_available():
            return False

        try:
            job_data = self._redis.hget(f"{self.QUEUE_KEY_PREFIX}:jobs", job_id)
            if not job_data:
                return False

            job = json.loads(job_data)
            job["status"] = status
            job["updated_at"] = datetime.now(timezone.utc).isoformat()

            if error:
                job["last_error"] = error
                job["retry_count"] = job.get("retry_count", 0) + 1

            # Update in hash
            self._redis.hset(f"{self.QUEUE_KEY_PREFIX}:jobs", job_id, json.dumps(job))

            # If completed or failed (max retries), remove from pending queue
            if status in ("completed", "failed"):
                # Find and remove from pending sorted set
                queue_key = f"{self.QUEUE_KEY_PREFIX}:pending"
                items = self._redis.zrange(queue_key, 0, -1, withscores=False)
                for item in items:
                    try:
                        item_job = json.loads(item)
                        if item_job.get("id") == job_id:
                            self._redis.zrem(queue_key, item)
                            break
                    except json.JSONDecodeError:
                        continue

                # Move to appropriate completed/failed queue
                if status == "completed":
                    completed_key = f"{self.QUEUE_KEY_PREFIX}:completed"
                    self._redis.lpush(completed_key, json.dumps(job))
                    # Trim completed queue to last 1000 items
                    self._redis.ltrim(completed_key, 0, 999)
                else:
                    failed_key = f"{self.QUEUE_KEY_PREFIX}:failed"
                    self._redis.lpush(failed_key, json.dumps(job))
                    self._redis.ltrim(failed_key, 0, 999)

            logger.debug("Updated operation %s status to %s", job_id, status)
            return True

        except Exception as e:
            logger.error("Failed to update operation %s: %s", job_id, e)
            return False

    def remove_operation(self, job_id: str) -> bool:
        """Remove an operation from the queue entirely."""
        if not self.is_available():
            return False

        try:
            # Remove from hash
            self._redis.hdel(f"{self.QUEUE_KEY_PREFIX}:jobs", job_id)

            # Remove from pending queue
            queue_key = f"{self.QUEUE_KEY_PREFIX}:pending"
            items = self._redis.zrange(queue_key, 0, -1, withscores=False)
            for item in items:
                try:
                    job = json.loads(item)
                    if job.get("id") == job_id:
                        self._redis.zrem(queue_key, item)
                        break
                except json.JSONDecodeError:
                    continue

            return True

        except Exception as e:
            logger.error("Failed to remove operation %s: %s", job_id, e)
            return False

    def get_queue_stats(self) -> dict:
        """Get statistics about the storage queue."""
        if not self.is_available():
            return {"available": False, "pending": 0, "completed": 0, "failed": 0}

        try:
            pending = self._redis.zcard(f"{self.QUEUE_KEY_PREFIX}:pending")
            completed = self._redis.llen(f"{self.QUEUE_KEY_PREFIX}:completed")
            failed = self._redis.llen(f"{self.QUEUE_KEY_PREFIX}:failed")

            return {
                "available": True,
                "pending": pending,
                "completed": completed,
                "failed": failed,
            }

        except Exception as e:
            logger.error("Failed to get queue stats: %s", e)
            return {"available": False, "pending": 0, "completed": 0, "failed": 0}

    def get_user_queue_stats(self, user_id: str) -> dict:
        """Get queue statistics for a specific user."""
        operations = self.get_pending_operations(user_id=user_id, limit=1000)

        return {
            "pending_count": len(operations),
            "operations": [
                {
                    "id": op["id"],
                    "type": op["operation_type"],
                    "created_at": op["created_at"],
                    "retry_count": op.get("retry_count", 0),
                    "status": op["status"],
                }
                for op in operations
            ],
        }


# Global queue service instance
_storage_queue: Optional[StorageQueueService] = None


def get_storage_queue() -> StorageQueueService:
    """Get the global storage queue service instance."""
    global _storage_queue
    if _storage_queue is None:
        _storage_queue = StorageQueueService()
    return _storage_queue
