from collections import defaultdict
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. Replace with Redis-backed limiter in production."""

    def __init__(self, app, calls: int = 100, period: int = 60) -> None:
        super().__init__(app)
        self.calls = calls
        self.period = period
        self._store: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time()
        window_start = now - self.period

        timestamps = [t for t in self._store[client_ip] if t > window_start]
        self._store[client_ip] = timestamps

        if len(timestamps) >= self.calls:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

        self._store[client_ip].append(now)
        return await call_next(request)
