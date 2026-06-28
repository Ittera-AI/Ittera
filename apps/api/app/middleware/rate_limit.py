"""Redis-backed sliding-window rate limiter.

Enforces a configurable per-client request limit using a shared Redis store so
that limits hold across every API process and replica (Requirement 5.3). The
limiter is tiered: requests to the authentication path prefix
(``/api/v1/auth/*`` by default) are held to a stricter limit than general
routes (Requirement 5.4), which protects credential endpoints from
brute-forcing. When a client exceeds its tier's limit within the window the
middleware short-circuits with HTTP 429 and a positive ``Retry-After`` header
(Requirements 5.1, 5.2, 5.5).

The window is implemented as a Redis sorted set per ``(tier, client)`` keyed by
client IP. Each request adds a uniquely-scored member at the current time;
entries older than the window are evicted, and the cardinality of the remaining
set is the rolling request count. All mutations run inside a single Redis
pipeline (MULTI/EXEC) so concurrent requests observe a consistent count.

If Redis is unreachable the limiter fails open (allows the request) and falls
back to a best-effort in-memory window for the current process, so a Redis
outage degrades protection rather than taking the API offline.

Reuses ``settings.REDIS_URL``; no new connection settings are introduced. Limits
are configurable via the ``RATE_LIMIT_*`` settings.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from __future__ import annotations

import logging
import math
import secrets
from collections import defaultdict
from time import time

import redis
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.config import settings

logger = logging.getLogger(__name__)

# Sorted-set key namespace. {tier} is "auth" or "general"; {client} is the IP.
_KEY = "ratelimit:{tier}:{client}"

# Tier identifiers.
_TIER_AUTH = "auth"
_TIER_GENERAL = "general"


class _Tier:
    """A single rate-limit tier: a request budget over a rolling window."""

    __slots__ = ("name", "max_requests", "window_seconds")

    def __init__(self, name: str, max_requests: int, window_seconds: int) -> None:
        self.name = name
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Shared-store sliding-window limiter with per-tier limits.

    Parameters default to the ``RATE_LIMIT_*`` application settings but may be
    overridden (e.g. in tests). A ``redis_client`` may be injected; otherwise a
    client is created lazily from ``settings.REDIS_URL``.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enabled: bool | None = None,
        general_max_requests: int | None = None,
        general_window_seconds: int | None = None,
        auth_max_requests: int | None = None,
        auth_window_seconds: int | None = None,
        auth_path_prefix: str | None = None,
        redis_client: "redis.Redis | None" = None,
    ) -> None:
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED if enabled is None else enabled
        self._general = _Tier(
            _TIER_GENERAL,
            settings.RATE_LIMIT_GENERAL_MAX_REQUESTS
            if general_max_requests is None
            else general_max_requests,
            settings.RATE_LIMIT_GENERAL_WINDOW_SECONDS
            if general_window_seconds is None
            else general_window_seconds,
        )
        self._auth = _Tier(
            _TIER_AUTH,
            settings.RATE_LIMIT_AUTH_MAX_REQUESTS
            if auth_max_requests is None
            else auth_max_requests,
            settings.RATE_LIMIT_AUTH_WINDOW_SECONDS
            if auth_window_seconds is None
            else auth_window_seconds,
        )
        self._auth_prefix = (
            settings.RATE_LIMIT_AUTH_PATH_PREFIX
            if auth_path_prefix is None
            else auth_path_prefix
        )
        self._injected_client = redis_client
        self._client: "redis.Redis | None" = redis_client
        # Best-effort per-process fallback used only when Redis is unreachable.
        self._fallback: dict[str, list[float]] = defaultdict(list)

    # -- client resolution ------------------------------------------------

    def _redis(self) -> "redis.Redis":
        if self._client is None:
            self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client

    def _tier_for(self, path: str) -> _Tier:
        if self._auth_prefix and path.startswith(self._auth_prefix):
            return self._auth
        return self._general

    @staticmethod
    def _client_id(request: Request) -> str:
        """Identify the client by IP, honoring a single proxy hop's forwarding."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First entry is the originating client when set by a trusted proxy.
            first = forwarded.split(",")[0].strip()
            if first:
                return first
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    # -- window evaluation ------------------------------------------------

    def _evaluate_redis(self, key: str, tier: _Tier, now: float) -> tuple[bool, int]:
        """Run the sliding-window check in Redis. Returns (allowed, retry_after)."""
        client = self._redis()
        window_start = now - tier.window_seconds
        member = f"{now:.6f}:{secrets.token_hex(8)}"

        pipe = client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {member: now})
        pipe.zcard(key)
        pipe.zrange(key, 0, 0, withscores=True)
        pipe.expire(key, tier.window_seconds)
        results = pipe.execute()

        count = int(results[2])
        oldest = results[3]

        if count > tier.max_requests:
            # Don't let blocked requests pile up in the window and starve recovery.
            client.zrem(key, member)
            retry_after = tier.window_seconds
            if oldest:
                oldest_score = float(oldest[0][1])
                retry_after = int(math.ceil(oldest_score + tier.window_seconds - now))
            return False, max(1, retry_after)

        return True, 0

    def _evaluate_fallback(self, key: str, tier: _Tier, now: float) -> tuple[bool, int]:
        """Best-effort in-memory window for the current process only."""
        window_start = now - tier.window_seconds
        timestamps = [t for t in self._fallback[key] if t > window_start]

        if len(timestamps) >= tier.max_requests:
            self._fallback[key] = timestamps
            oldest_score = timestamps[0]
            retry_after = int(math.ceil(oldest_score + tier.window_seconds - now))
            return False, max(1, retry_after)

        timestamps.append(now)
        self._fallback[key] = timestamps
        return True, 0

    # -- dispatch ---------------------------------------------------------

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        tier = self._tier_for(request.url.path)
        key = _KEY.format(tier=tier.name, client=self._client_id(request))
        now = time()

        try:
            allowed, retry_after = await run_in_threadpool(
                self._evaluate_redis, key, tier, now
            )
        except redis.RedisError as exc:
            # Fail open: a Redis outage must not take the API down. Degrade to a
            # per-process window so some protection remains.
            logger.warning("Rate limiter Redis unavailable, using in-memory fallback: %s", exc)
            allowed, retry_after = self._evaluate_fallback(key, tier, now)

        if not allowed:
            return self._rate_limited_response(retry_after)

        return await call_next(request)

    @staticmethod
    def _rate_limited_response(retry_after: int) -> Response:
        retry_after = max(1, int(retry_after))
        return JSONResponse(
            {"detail": "Rate limit exceeded. Please retry later."},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
