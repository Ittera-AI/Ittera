"""
Structured logging configuration with secret redaction.

This module provides the JSON logging stack for the API:

- ``correlation_id_var`` — a ``contextvar`` holding the active request's
  correlation id. ``CorrelationIdMiddleware`` binds it per request so that any
  log record emitted while handling the request carries the same id, letting a
  client report be matched to server logs. (R11.1, R11.4)
- ``JsonLogFormatter`` — renders each log record as a single JSON line including
  the correlation id, severity, and timestamp. (R11.1)
- ``SecretRedactingFormatter`` — a ``JsonLogFormatter`` that scrubs secret-like
  values from log output. It reuses ``app.core.audit_logger.SENSITIVE_KEYS`` as
  the single source of truth for which keys are redacted, so logs and audit
  details redact the same set. (R4.4, R7.2)
- ``configure_logging`` — installs the redacting JSON formatter on the root
  logger.

The formatter never raises: logging must not be able to crash request handling.
"""

import contextvars
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.audit_logger import SENSITIVE_KEYS

# ---------------------------------------------------------------------------
# Correlation id context
# ---------------------------------------------------------------------------

# Bound per request by CorrelationIdMiddleware (FX-5, task 4.1). Defaults to None
# for log records emitted outside a request (startup, background tasks, etc.).
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def get_correlation_id() -> Optional[str]:
    """Return the correlation id bound to the current context, if any."""
    return correlation_id_var.get()


def set_correlation_id(value: Optional[str]) -> contextvars.Token:
    """Bind a correlation id to the current context and return the reset token."""
    return correlation_id_var.set(value)


def reset_correlation_id(token: contextvars.Token) -> None:
    """Restore the correlation id to its previous value using ``token``."""
    correlation_id_var.reset(token)


# ---------------------------------------------------------------------------
# Redaction helpers (reuse the audit logger's sensitive-key set)
# ---------------------------------------------------------------------------

REDACTED = "[REDACTED]"

# Standard ``LogRecord`` attributes that should not be treated as structured
# "extra" fields when serialising a record.
_RESERVED_RECORD_ATTRS = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "taskName", "message", "asctime",
    }
)


def _key_is_sensitive(key: str) -> bool:
    """Mirror the audit logger's substring match against ``SENSITIVE_KEYS``."""
    lower_key = key.lower()
    return any(token in lower_key for token in SENSITIVE_KEYS)


def redact_structure(value: Any) -> Any:
    """
    Recursively redact sensitive values from a mapping/list structure.

    Uses the same substring matching rule as ``AuditLogger._sanitize_details``
    so structured log fields redact exactly the keys the audit logger redacts.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if isinstance(key, str) and _key_is_sensitive(key):
                result[key] = REDACTED
            else:
                result[key] = redact_structure(item)
        return result
    if isinstance(value, (list, tuple)):
        return [redact_structure(item) for item in value]
    return value


# Matches ``key: value`` / ``key=value`` pairs in free-text messages where the
# key contains one of the sensitive substrings, so secrets embedded in a log
# string (e.g. ``access_token=abc123``) are scrubbed as well as structured ones.
_SECRET_PATTERN = re.compile(
    r"(?i)"
    r"([\"']?[\w.-]*(?:" + "|".join(re.escape(k) for k in sorted(SENSITIVE_KEYS)) + r")[\w.-]*[\"']?"
    r"\s*[:=]\s*)"
    r"([\"']?)"
    r"([^\s,;}\"']+)"
)


def redact_text(message: str) -> str:
    """Redact ``key: value`` secret pairs embedded in a free-text message."""
    return _SECRET_PATTERN.sub(lambda m: f"{m.group(1)}{m.group(2)}{REDACTED}", message)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


class JsonLogFormatter(logging.Formatter):
    """Render a log record as a single JSON line.

    Always includes ``timestamp`` (ISO 8601 UTC), ``severity``, ``logger``, and
    ``message``. Includes ``correlation_id`` when one is bound to the context,
    any structured ``extra`` fields, and exception info when present.
    """

    def _build_payload(self, record: logging.LogRecord) -> dict:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = get_correlation_id()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        # Surface any structured extras passed via logger(..., extra={...}).
        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_ATTRS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return payload

    def format(self, record: logging.LogRecord) -> str:
        try:
            payload = self._build_payload(record)
            return json.dumps(payload, default=str)
        except Exception:  # logging must never crash the caller
            return json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": getattr(record, "levelname", "ERROR"),
                    "logger": getattr(record, "name", "unknown"),
                    "message": "log formatting error",
                }
            )


class SecretRedactingFormatter(JsonLogFormatter):
    """A ``JsonLogFormatter`` that redacts secret-like values from output.

    Reuses ``SENSITIVE_KEYS`` (the audit logger's redaction key set) so that
    structured fields and ``key: value`` pairs embedded in messages are scrubbed
    before the record is written. (R4.4, R7.2)
    """

    def _build_payload(self, record: logging.LogRecord) -> dict:
        payload = super()._build_payload(record)

        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(key, str) and _key_is_sensitive(key):
                redacted[key] = REDACTED
            elif key == "message" and isinstance(value, str):
                redacted[key] = redact_text(value)
            else:
                redacted[key] = redact_structure(value)
        return redacted


# ---------------------------------------------------------------------------
# Configuration entry point
# ---------------------------------------------------------------------------


def configure_logging(level: int | str = logging.INFO) -> None:
    """Install the redacting JSON formatter on the root logger.

    Idempotent: replaces the formatter on the existing root handler (or adds a
    single stream handler if none exists) rather than stacking handlers.
    """
    formatter = SecretRedactingFormatter()
    root = logging.getLogger()
    root.setLevel(level)

    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setFormatter(formatter)
