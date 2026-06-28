"""
Audit Logger — comprehensive logging for security and compliance.

Tracks all access and modifications to user data for:
- Security auditing
- GDPR compliance
- User transparency
- Debugging and forensics

Uses structured logging for easy parsing and analysis.
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

# Separate logger for audit events
audit_logger = logging.getLogger("iterra.audit")

# Canonical set of substrings that mark a key as carrying sensitive data.
# A key is considered sensitive when any of these substrings appears in its
# lowercased name (e.g. "user_access_token" matches "access_token").
#
# This is the single source of truth for secret redaction across the app: the
# structured logging layer (see ``app.core.logging``) imports this set so log
# output and audit details redact the same keys.
SENSITIVE_KEYS = frozenset(
    {
        "password", "token", "access_token", "refresh_token",
        "api_key", "secret", "credential", "auth",
    }
)


class AuditAction(str, Enum):
    """Types of audit actions."""

    # Storage operations
    STORAGE_READ = "storage:read"
    STORAGE_WRITE = "storage:write"
    STORAGE_DELETE = "storage:delete"
    STORAGE_EXPORT = "storage:export"
    STORAGE_IMPORT = "storage:import"

    # Auth operations
    AUTH_LOGIN = "auth:login"
    AUTH_LOGOUT = "auth:logout"
    AUTH_TOKEN_REFRESH = "auth:token_refresh"
    AUTH_PASSWORD_CHANGE = "auth:password_change"

    # OAuth operations
    OAUTH_CONNECT = "oauth:connect"
    OAUTH_DISCONNECT = "oauth:disconnect"
    OAUTH_REVOKE = "oauth:revoke"

    # Data operations
    DATA_CREATE = "data:create"
    DATA_UPDATE = "data:update"
    DATA_DELETE = "data:delete"
    DATA_LIST = "data:list"

    # Privacy operations
    PRIVACY_EXPORT = "privacy:export"
    PRIVACY_DELETE = "privacy:delete"
    PRIVACY_SETTINGS_CHANGE = "privacy:settings_change"

    # Admin operations
    ADMIN_ACCESS = "admin:access"
    ADMIN_USER_VIEW = "admin:user_view"
    ADMIN_USER_MODIFY = "admin:user_modify"


class AuditLogLevel(str, Enum):
    """Audit log severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Structured audit logger for security and compliance.

    Every audit log entry includes:
    - event_id: Unique identifier for the event
    - timestamp: ISO 8601 timestamp
    - action: The action being performed
    - user_id: User who performed the action
    - resource_type: Type of resource accessed
    - resource_id: ID of the resource
    - status: Success or failure
    - details: Additional context (sanitized)
    - ip_address: Client IP (if available)
    - user_agent: Client user agent (if available)
    """

    def __init__(self):
        self.logger = audit_logger

    def _sanitize_details(self, details: Optional[dict]) -> dict:
        """
        Sanitize sensitive data from audit log details.

        Removes or masks:
        - Passwords
        - Tokens
        - API keys
        - PII (emails, phone numbers)
        """
        if not details:
            return {}

        sanitized = {}
        sensitive_keys = SENSITIVE_KEYS

        for key, value in details.items():
            lower_key = key.lower()

            # Check if key is sensitive
            if any(s in lower_key for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    def log(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        details: Optional[dict] = None,
        level: AuditLogLevel = AuditLogLevel.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Log an audit event.

        Args:
            action: The action being performed
            user_id: User who performed the action
            resource_type: Type of resource accessed
            resource_id: ID of the resource
            status: Success or failure
            details: Additional context (will be sanitized)
            level: Log severity level
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            The event ID
        """
        event_id = str(uuid4())

        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "status": status,
            "details": self._sanitize_details(details),
            "level": level.value,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }

        # Log with appropriate level
        log_message = json.dumps(log_entry, default=str)

        if level == AuditLogLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == AuditLogLevel.ERROR:
            self.logger.error(log_message)
        elif level == AuditLogLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        return event_id

    # Convenience methods for common operations

    def storage_read(
        self,
        user_id: str,
        file_id: str,
        file_name: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log a storage read operation."""
        return self.log(
            action=AuditAction.STORAGE_READ,
            user_id=user_id,
            resource_type="drive_file",
            resource_id=file_id,
            status="success" if success else "failure",
            details={"file_name": file_name, "error": error},
            level=AuditLogLevel.ERROR if not success else AuditLogLevel.INFO,
            **kwargs,
        )

    def storage_write(
        self,
        user_id: str,
        file_id: str,
        file_name: str,
        operation: str = "create",  # create or update
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log a storage write operation."""
        return self.log(
            action=AuditAction.STORAGE_WRITE,
            user_id=user_id,
            resource_type="drive_file",
            resource_id=file_id,
            status="success" if success else "failure",
            details={"file_name": file_name, "operation": operation, "error": error},
            level=AuditLogLevel.ERROR if not success else AuditLogLevel.INFO,
            **kwargs,
        )

    def storage_delete(
        self,
        user_id: str,
        file_id: str,
        file_name: Optional[str] = None,
        success: bool = True,
        **kwargs,
    ) -> str:
        """Log a storage delete operation."""
        return self.log(
            action=AuditAction.STORAGE_DELETE,
            user_id=user_id,
            resource_type="drive_file",
            resource_id=file_id,
            status="success" if success else "failure",
            details={"file_name": file_name},
            level=AuditLogLevel.WARNING,  # Deletes are always logged as warnings
            **kwargs,
        )

    def storage_export(
        self,
        user_id: str,
        total_files: int,
        total_drafts: int,
        success: bool = True,
        **kwargs,
    ) -> str:
        """Log a data export operation (GDPR Article 20)."""
        return self.log(
            action=AuditAction.STORAGE_EXPORT,
            user_id=user_id,
            resource_type="user_data",
            resource_id=user_id,
            status="success" if success else "failure",
            details={
                "total_files": total_files,
                "total_drafts": total_drafts,
                "purpose": "gdpr_data_portability",
            },
            level=AuditLogLevel.INFO,
            **kwargs,
        )

    def storage_import(
        self,
        user_id: str,
        drafts_imported: int,
        drafts_skipped: int,
        success: bool = True,
        **kwargs,
    ) -> str:
        """Log a data import operation."""
        return self.log(
            action=AuditAction.STORAGE_IMPORT,
            user_id=user_id,
            resource_type="user_data",
            resource_id=user_id,
            status="success" if success else "failure",
            details={
                "drafts_imported": drafts_imported,
                "drafts_skipped": drafts_skipped,
            },
            level=AuditLogLevel.INFO,
            **kwargs,
        )

    def oauth_connect(
        self,
        user_id: str,
        platform: str,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log an OAuth connection."""
        return self.log(
            action=AuditAction.OAUTH_CONNECT,
            user_id=user_id,
            resource_type="oauth_connection",
            resource_id=platform,
            status="success" if success else "failure",
            details={"platform": platform, "error": error},
            level=AuditLogLevel.INFO if success else AuditLogLevel.WARNING,
            **kwargs,
        )

    def oauth_disconnect(
        self,
        user_id: str,
        platform: str,
        reason: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Log an OAuth disconnection."""
        return self.log(
            action=AuditAction.OAUTH_DISCONNECT,
            user_id=user_id,
            resource_type="oauth_connection",
            resource_id=platform,
            status="success",
            details={"platform": platform, "reason": reason},
            level=AuditLogLevel.WARNING,  # Disconnections are notable events
            **kwargs,
        )

    def privacy_data_delete(
        self,
        user_id: str,
        deleted_files: int,
        db_records_cleared: bool,
        **kwargs,
    ) -> str:
        """Log a GDPR data deletion request."""
        return self.log(
            action=AuditAction.PRIVACY_DELETE,
            user_id=user_id,
            resource_type="user_data",
            resource_id=user_id,
            status="success",
            details={
                "deleted_files": deleted_files,
                "db_records_cleared": db_records_cleared,
                "gdpr_article": 17,  # Right to erasure
            },
            level=AuditLogLevel.WARNING,  # Data deletion is a significant event
            **kwargs,
        )

    def privacy_settings_change(
        self,
        user_id: str,
        setting_name: str,
        old_value: Any,
        new_value: Any,
        **kwargs,
    ) -> str:
        """Log a privacy settings change."""
        return self.log(
            action=AuditAction.PRIVACY_SETTINGS_CHANGE,
            user_id=user_id,
            resource_type="privacy_settings",
            resource_id=setting_name,
            status="success",
            details={
                "setting": setting_name,
                "old_value": str(old_value) if old_value else None,
                "new_value": str(new_value) if new_value else None,
            },
            level=AuditLogLevel.INFO,
            **kwargs,
        )


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
