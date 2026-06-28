import logging
import os

import redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

import app.models  # noqa: F401
from app.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import (
    analytics,
    approvals,
    auth,
    brand_profile,
    calendar,
    coach,
    content,
    context,
    linkedin,
    onboarding,
    organizations,
    persona,
    predictions,
    radar,
    repurpose,
    reports,
    social,
    social_oauth,
    storage,
    sync,
    trends,
    users,
    workspaces,
)
from app.routers import competitors, waitlist

# Install the structured, secret-redacting JSON logging stack before anything
# emits a log record so startup and request logs share the same format (R11.1).
configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Iterra API",
    version="0.1.0",
    description="AI Content Strategy Platform API",
)

# Register the global exception/validation/HTTPException handlers so every error
# returns the standardized, correlated Error_Envelope (R7.1).
register_exception_handlers(app)

# --- Middleware stack (FX-8) ------------------------------------------------
# Starlette runs middleware in the REVERSE order of registration: the last one
# added is the outermost (runs first on the way in). To get the effective
# request order CorrelationId -> CORS -> RateLimit we therefore register them
# in the opposite order: RateLimit first, then CORS, then CorrelationId last.
# This guarantees a correlation id is bound before CORS/limiting run, and the
# rate limiter sits closest to the route handlers.

# Innermost: rate limiting (runs last, just before the route). R5.1
app.add_middleware(RateLimitMiddleware)

# Middle: CORS. In production, restrict the allowed methods/headers to what the
# API actually uses instead of the permissive "*" wildcard. Origins are always
# the configured allowlist (never "*"), which is required when
# allow_credentials is True. R6.2
_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"] if _IS_PRODUCTION else ["*"],
    allow_headers=["Authorization", "Content-Type"] if _IS_PRODUCTION else ["*"],
)

# Outermost: correlation id (runs first), so every downstream layer — including
# CORS, the limiter, handlers, and logs — sees a bound correlation id. R11.4
app.add_middleware(CorrelationIdMiddleware)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
app.include_router(linkedin.router, prefix="/api/v1/linkedin", tags=["linkedin"])
app.include_router(brand_profile.router, prefix="/api/v1/brand-profile", tags=["brand-profile"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(waitlist.router, prefix="/api/v1/waitlist", tags=["waitlist"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["calendar"])
app.include_router(repurpose.router, prefix="/api/v1/repurpose", tags=["repurpose"])
app.include_router(coach.router, prefix="/api/v1/coach", tags=["coach"])
app.include_router(radar.router, prefix="/api/v1/radar", tags=["radar"])
app.include_router(social.router, prefix="/api/v1/social", tags=["social"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])
app.include_router(social_oauth.router, prefix="/api/v1/connect", tags=["connect"])
app.include_router(persona.router, prefix="/api/v1/persona", tags=["persona"])
app.include_router(storage.router, prefix="/api/v1/storage", tags=["storage"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["predictions"])
app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["competitors"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(approvals.router, prefix="/api/v1/approvals", tags=["approvals"])


def _check_database() -> bool:
    """Run a trivial ``SELECT 1`` to confirm the database is reachable."""
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        # Category-only result: the specific driver/exception detail stays in
        # logs and never reaches the readiness response body. (R11.3)
        logger.warning("Readiness check: database unreachable", exc_info=True)
        return False
    finally:
        session.close()


def _check_broker() -> bool:
    """Ping the Celery broker (Redis) to confirm it is reachable."""
    client = None
    try:
        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        return bool(client.ping())
    except Exception:
        logger.warning("Readiness check: broker unreachable", exc_info=True)
        return False
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def _liveness_payload() -> dict:
    """Process-only liveness payload (no dependency checks)."""
    return {"status": "ok", "service": "iterra-api"}


@app.get("/health", tags=["health"])
async def health_check():
    """Liveness alias retained for backward compatibility (nginx, tests)."""
    return _liveness_payload()


@app.get("/health/live", tags=["health"])
async def liveness_probe():
    """Liveness_Probe: reports process health without checking dependencies. (R11.2)"""
    return _liveness_payload()


@app.get("/health/ready", tags=["health"])
async def readiness_probe():
    """Readiness_Probe: ready only if the DB and broker are both reachable. (R11.3)

    Runs a DB ``SELECT 1`` and a broker ping. When either is unreachable the
    probe returns HTTP 503 with a category-only failure detail (which dependency
    failed), never the underlying exception or connection string.
    """
    db_ok, broker_ok = await run_in_threadpool(
        lambda: (_check_database(), _check_broker())
    )

    checks = {
        "database": "ok" if db_ok else "unavailable",
        "broker": "ok" if broker_ok else "unavailable",
    }

    if db_ok and broker_ok:
        return {"status": "ready", "service": "iterra-api", "checks": checks}

    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "service": "iterra-api", "checks": checks},
    )
