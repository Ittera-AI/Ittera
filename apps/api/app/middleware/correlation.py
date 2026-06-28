"""Correlation ID middleware.

Assigns or propagates a per-request ``X-Correlation-ID``, binds it to a
``contextvar`` so loggers and exception handlers can read it without threading
the value through call signatures, and echoes it on every response.

Requirements: 11.1, 11.4, 7.4
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from iterra_ai.core.cost_tracker import reset_request_id as reset_cost_request_id
from iterra_ai.core.cost_tracker import set_request_id as set_cost_request_id
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# Header used to carry the correlation id across the request/response boundary.
CORRELATION_ID_HEADER = "X-Correlation-ID"

# Request-scoped storage for the active correlation id. Loggers and exception
# handlers read from here so the same id appears in logs and the error envelope.
_correlation_id_ctx: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)

# Inbound ids longer than this are treated as untrusted and replaced with a
# freshly generated id to avoid unbounded values leaking into logs/headers.
_MAX_CORRELATION_ID_LENGTH = 128


def get_correlation_id() -> str | None:
    """Return the correlation id bound to the current request context, if any."""
    return _correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> object:
    """Bind ``correlation_id`` to the current context and return the reset token."""
    return _correlation_id_ctx.set(correlation_id)


def _is_valid_inbound_id(value: str) -> bool:
    """Accept a non-empty, length-bounded inbound id; otherwise generate a new one."""
    stripped = value.strip()
    return bool(stripped) and len(stripped) <= _MAX_CORRELATION_ID_LENGTH


def generate_correlation_id() -> str:
    """Generate a new opaque correlation id."""
    return uuid.uuid4().hex


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assign/propagate a correlation id and echo it on every response.

    On each request the middleware reuses a valid inbound ``X-Correlation-ID``
    header (propagated unchanged) or generates a new one. The id is bound to a
    ``contextvar`` for the duration of the request and written to the response
    header, including on error responses.
    """

    def __init__(self, app: ASGIApp, header_name: str = CORRELATION_ID_HEADER) -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        inbound = request.headers.get(self.header_name)
        if inbound is not None and _is_valid_inbound_id(inbound):
            correlation_id = inbound.strip()
        else:
            correlation_id = generate_correlation_id()

        # Expose to downstream handlers via request state and the contextvar.
        request.state.correlation_id = correlation_id
        token = set_correlation_id(correlation_id)
        # Attribute any AI engine LLM calls made while handling this request to
        # the same correlation id, so cost can be matched per request (R11.5).
        cost_token = set_cost_request_id(correlation_id)

        try:
            response: Response = await call_next(request)
        finally:
            _correlation_id_ctx.reset(token)
            reset_cost_request_id(cost_token)

        response.headers[self.header_name] = correlation_id
        return response
