"""
Global error handling and the standardized ``Error_Envelope``.

This module centralizes how the API turns errors into responses so that every
client sees one consistent, sanitized shape and every error can be matched back
to server logs via the correlation id.

Three handlers are provided (registered onto the app in ``main.py``, task 7.1):

- ``unhandled_exception_handler`` — any uncaught ``Exception`` becomes an HTTP
  500 ``Error_Envelope`` with ``code="internal_error"``. The stack trace and
  exception detail are logged to the server log only; the response body carries
  no stack trace, exception message, or internal identifier. (R7.1, R7.4)
- ``validation_exception_handler`` — a ``RequestValidationError`` becomes an HTTP
  422 ``Error_Envelope`` with ``code="validation_error"`` and field-level
  ``details``. Offending values are never echoed and secret-like field names get
  a generic issue, so no secret value leaks. (R7.2, R7.3)
- ``http_exception_handler`` — an ``HTTPException`` (401/403/404/429 and others)
  is wrapped in the same envelope, preserving the original status code and any
  response headers (e.g. ``Retry-After`` on 429). (R7.4)

Every envelope includes the correlation id, which matches the
``X-Correlation-ID`` response header set by ``CorrelationIdMiddleware``. The
handlers resolve that id from ``request.state`` first (where the middleware
stores it) and fall back to the correlation contextvars. (R7.4)

The ``Error_Envelope`` shape (see design):

    {
      "error": {
        "code": "internal_error | validation_error | not_found | "
                "unauthorized | forbidden | rate_limited | ...",
        "message": "category-level message with no internal detail",
        "correlation_id": "8f3c...",
        "details": [ { "field": "scheduled_for", "issue": "must be ..." } ]
      }
    }
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import (
    _key_is_sensitive,
    get_correlation_id as _logging_correlation_id,
    redact_text,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Error codes and category-level messages
# ---------------------------------------------------------------------------

CODE_INTERNAL_ERROR = "internal_error"
CODE_VALIDATION_ERROR = "validation_error"
CODE_NOT_FOUND = "not_found"
CODE_UNAUTHORIZED = "unauthorized"
CODE_FORBIDDEN = "forbidden"
CODE_RATE_LIMITED = "rate_limited"
CODE_BAD_REQUEST = "bad_request"
CODE_CONFLICT = "conflict"
CODE_ERROR = "error"

# Maps an HTTP status code to the envelope ``code`` it should carry.
_STATUS_CODE_MAP: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: CODE_BAD_REQUEST,
    status.HTTP_401_UNAUTHORIZED: CODE_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN: CODE_FORBIDDEN,
    status.HTTP_404_NOT_FOUND: CODE_NOT_FOUND,
    status.HTTP_409_CONFLICT: CODE_CONFLICT,
    status.HTTP_422_UNPROCESSABLE_ENTITY: CODE_VALIDATION_ERROR,
    status.HTTP_429_TOO_MANY_REQUESTS: CODE_RATE_LIMITED,
}

# Category-level message per code. These never contain internal detail.
_CODE_MESSAGE: dict[str, str] = {
    CODE_INTERNAL_ERROR: "An internal error occurred.",
    CODE_VALIDATION_ERROR: "Request validation failed.",
    CODE_NOT_FOUND: "The requested resource was not found.",
    CODE_UNAUTHORIZED: "Authentication is required or has failed.",
    CODE_FORBIDDEN: "You do not have permission to perform this action.",
    CODE_RATE_LIMITED: "Too many requests.",
    CODE_BAD_REQUEST: "The request could not be processed.",
    CODE_CONFLICT: "The request conflicts with the current state.",
    CODE_ERROR: "The request could not be completed.",
}

# Location markers Pydantic/FastAPI prepend to a validation error ``loc`` that
# are not part of the user-facing field path.
_LOC_MARKERS = frozenset({"body", "query", "path", "header", "cookie"})


# ---------------------------------------------------------------------------
# Correlation id resolution
# ---------------------------------------------------------------------------


def _resolve_correlation_id(request: Optional[Request]) -> Optional[str]:
    """Resolve the correlation id that matches the ``X-Correlation-ID`` header.

    Prefers the value ``CorrelationIdMiddleware`` stored on ``request.state``,
    then the middleware's contextvar, then the logging contextvar. This keeps
    the envelope's ``correlation_id`` identical to the response header.
    """
    if request is not None:
        state_id = getattr(request.state, "correlation_id", None)
        if state_id:
            return state_id

    try:  # avoid a hard import cycle at module load time
        from app.middleware.correlation import get_correlation_id as _mw_correlation_id

        mw_id = _mw_correlation_id()
        if mw_id:
            return mw_id
    except Exception:  # pragma: no cover - defensive only
        pass

    return _logging_correlation_id()


# ---------------------------------------------------------------------------
# Envelope construction
# ---------------------------------------------------------------------------


def _code_for_status(status_code: int) -> str:
    """Return the envelope ``code`` for an HTTP status code."""
    if status_code in _STATUS_CODE_MAP:
        return _STATUS_CODE_MAP[status_code]
    if status_code >= 500:
        return CODE_INTERNAL_ERROR
    return CODE_ERROR


def build_error_envelope(
    code: str,
    message: str,
    correlation_id: Optional[str],
    details: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Build the standardized ``Error_Envelope`` body."""
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "correlation_id": correlation_id,
    }
    if details is not None:
        error["details"] = details
    return {"error": error}


def _field_from_loc(loc: Any) -> str:
    """Derive a user-facing field path from a validation error ``loc`` tuple."""
    if not isinstance(loc, (list, tuple)):
        return str(loc)

    parts = [str(part) for part in loc]
    # Drop the leading location marker (e.g. "body") when a field follows it.
    if parts and parts[0] in _LOC_MARKERS and len(parts) > 1:
        parts = parts[1:]
    return ".".join(parts) if parts else "__root__"


def _build_validation_details(
    exc: RequestValidationError,
) -> list[dict[str, Any]]:
    """Build secret-safe, field-level details for a validation error.

    Never includes the offending input value. For secret-like field names the
    issue is replaced with a generic message; for other fields the validation
    message is included after redacting any embedded ``key: value`` secrets.
    """
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        field = _field_from_loc(err.get("loc", ()))
        if _key_is_sensitive(field):
            issue = "invalid value"
        else:
            raw_issue = str(err.get("msg") or "invalid value")
            issue = redact_text(raw_issue)
        details.append({"field": field, "issue": issue})
    return details


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a sanitized HTTP 500 envelope for any uncaught exception.

    The exception class and stack trace are logged to the server log only; the
    response body contains no stack trace, exception message, or internal id.
    """
    correlation_id = _resolve_correlation_id(request)

    # Server-side log carries the detail; the client response never does.
    logger.error(
        "Unhandled exception: %s",
        exc.__class__.__name__,
        exc_info=exc,
        extra={"correlation_id": correlation_id},
    )

    envelope = build_error_envelope(
        code=CODE_INTERNAL_ERROR,
        message=_CODE_MESSAGE[CODE_INTERNAL_ERROR],
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=envelope
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return an HTTP 422 envelope with secret-safe field-level details."""
    correlation_id = _resolve_correlation_id(request)
    details = _build_validation_details(exc)

    envelope = build_error_envelope(
        code=CODE_VALIDATION_ERROR,
        message=_CODE_MESSAGE[CODE_VALIDATION_ERROR],
        correlation_id=correlation_id,
        details=details,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=envelope
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Wrap an ``HTTPException`` in the standard envelope, preserving status.

    The original status code and any response headers (e.g. ``Retry-After`` on a
    429, ``WWW-Authenticate`` on a 401) are preserved. The detail message is
    redacted of any embedded secrets, falling back to the category message when
    no usable detail is present.
    """
    correlation_id = _resolve_correlation_id(request)
    code = _code_for_status(exc.status_code)

    detail = exc.detail
    if isinstance(detail, str) and detail.strip():
        message = redact_text(detail)
    else:
        message = _CODE_MESSAGE.get(code, _CODE_MESSAGE[CODE_ERROR])

    envelope = build_error_envelope(
        code=code,
        message=message,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope,
        headers=getattr(exc, "headers", None),
    )


# ---------------------------------------------------------------------------
# Registration helper (called from main.py in task 7.1)
# ---------------------------------------------------------------------------


def register_exception_handlers(app: FastAPI) -> None:
    """Register the global exception handlers onto ``app``.

    Intended to be called from ``main.py`` (task 7.1). Registers handlers for
    uncaught ``Exception``, ``RequestValidationError``, and ``HTTPException``
    (both the FastAPI and Starlette variants resolve to ``StarletteHTTPException``).
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
