from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    """Optional JWT middleware for global auth enforcement.
    Per-route auth is handled via get_current_user dependency."""

    EXEMPT_PATHS = {"/health", "/api/v1/auth/login", "/api/v1/auth/register", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        return await call_next(request)
