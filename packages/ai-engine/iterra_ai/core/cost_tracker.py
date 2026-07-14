"""Per-call LLM cost attribution.

Every outbound LLM call routes through ``BaseEngine._call_llm``, which records
token usage here. Usage is attributed to the active request/correlation id so
cost can be matched back to the originating request (Requirement 11.5).

The active request id is held in a module-level :class:`ContextVar`. The hosting
application (e.g. the FastAPI backend) binds its per-request correlation id with
:func:`set_request_id` so that any engine call made while handling that request
is attributed to it, without threading the id through engine call signatures.
"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass

logger = logging.getLogger("iterra_ai.cost")

INPUT_COST_PER_1K = 0.003
OUTPUT_COST_PER_1K = 0.015

# Request-scoped storage for the active request/correlation id. Set by the
# hosting application per request; read here when usage is logged.
_request_id_ctx: ContextVar[str | None] = ContextVar(
    "iterra_ai_request_id", default=None
)


def set_request_id(request_id: str | None) -> object:
    """Bind ``request_id`` to the current context and return the reset token."""
    return _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    """Return the request/correlation id bound to the current context, if any."""
    return _request_id_ctx.get()


def reset_request_id(token: object) -> None:
    """Reset the request id context var using the token from :func:`set_request_id`."""
    _request_id_ctx.reset(token)  # type: ignore[arg-type]


@dataclass(frozen=True)
class UsageLog:
    engine: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    request_id: str | None = None


class CostTracker:
    def log(
        self,
        engine: str,
        input_tokens: int,
        output_tokens: int,
        request_id: str | None = None,
    ) -> UsageLog:
        # Prefer an explicitly supplied id; otherwise attribute to the active
        # request/correlation id bound by the hosting application.
        resolved_request_id = request_id if request_id is not None else get_request_id()
        cost = (input_tokens / 1000 * INPUT_COST_PER_1K) + (
            output_tokens / 1000 * OUTPUT_COST_PER_1K
        )
        entry = UsageLog(
            engine=engine,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            request_id=resolved_request_id,
        )
        logger.info(
            "LLM_USAGE engine=%s request_id=%s input_tokens=%d output_tokens=%d cost_usd=%.6f",
            engine,
            resolved_request_id or "-",
            input_tokens,
            output_tokens,
            cost,
        )
        return entry
