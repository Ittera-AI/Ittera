import os
import socket as _socket_module
import sys
from pathlib import Path

# Disable rate limiting for the whole test session BEFORE importing main.
# RateLimitMiddleware reads settings.RATE_LIMIT_ENABLED at construction time in
# main.py (imported below), and main is imported at module load. During tests
# there is no Redis, so the middleware uses an in-memory fallback whose state
# persists across the shared session TestClient/app; the strict auth tier
# (10 req/60s) would otherwise cause /api/v1/auth/* tests to receive HTTP 429.
# This only affects the test harness — production defaults are untouched.
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
import httpx
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import app.db.session as db_session
from app.config import settings
from app.db.base import Base
from app.dependencies.db import get_db
from main import app

# Belt-and-suspenders: ensure the already-instantiated settings object also has
# rate limiting disabled, in case it was constructed before the env var was read.
settings.RATE_LIMIT_ENABLED = False

# Run Celery tasks inline (no broker) so publish paths that enqueue
# on_post_published via .delay() don't block on a Redis connection during tests.
from workers.celery.app import celery_app as _celery_app

_celery_app.conf.task_always_eager = True
_celery_app.conf.task_eager_propagates = False
_celery_app.conf.broker_url = "memory://"
_celery_app.conf.result_backend = "cache+memory://"

# A single in-memory SQLite shared across the whole test session. StaticPool keeps
# one underlying connection alive, so the schema — and any data committed during a
# test — is visible to EVERY session, including services/workers that open their own
# SessionLocal() directly. This eliminates the cross-module "no such table: users"
# flake that occurred with a file-backed test.db plus a separate, non-app engine.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Rebind the app's shared sessionmaker so every caller uses the test engine:
#  - routes via get_db (also explicitly overridden below)
#  - any service/Celery task that imported SessionLocal and calls it directly
# dependencies/db.py and core/database.py hold a reference to this same object,
# so reconfiguring its bind updates them too.
db_session.engine = engine
db_session.SessionLocal.configure(bind=engine)
TestingSessionLocal = db_session.SessionLocal


# ---------------------------------------------------------------------------
# Network isolation (R13.1)
# ---------------------------------------------------------------------------
# pytest-socket (configured in pytest.ini via --disable-socket) already blocks
# raw sockets to non-loopback hosts. This autouse fixture is a second, defensive
# layer that fails fast if any code path tries to open a *real* httpx connection
# (Supabase / LinkedIn / Twitter / Google / SMTP). The in-process ASGI transport
# used by FastAPI's TestClient is a different transport class and is left intact,
# and the in-memory SQLite database does not use sockets at all.
class _NetworkBlockedError(RuntimeError):
    """Raised when a test attempts a real outbound network connection."""


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Patch httpx/socket transports to raise on any real outbound connection.

    Permits:
      - FastAPI TestClient's in-process ASGITransport (different class, untouched)
      - In-memory SQLite (no sockets)
      - Loopback sockets (127.0.0.1/::1) for any local fixtures
    """

    def _blocked_sync(self, request, *args, **kwargs):  # noqa: ANN001
        raise _NetworkBlockedError(
            f"Real network access is blocked in tests: {request.method} {request.url}"
        )

    async def _blocked_async(self, request, *args, **kwargs):  # noqa: ANN001
        raise _NetworkBlockedError(
            f"Real network access is blocked in tests: {request.method} {request.url}"
        )

    # httpx real-network transports — the in-process ASGITransport is NOT patched,
    # so the TestClient keeps working.
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", _blocked_sync, raising=True)
    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", _blocked_async, raising=True
    )

    # Defensive guard on the low-level socket connect for non-loopback hosts.
    _real_connect = _socket_module.socket.connect

    def _guarded_connect(self, address, *args, **kwargs):  # noqa: ANN001
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            raise _NetworkBlockedError(f"Real socket connection blocked in tests: {address}")
        return _real_connect(self, address, *args, **kwargs)

    monkeypatch.setattr(_socket_module.socket, "connect", _guarded_connect, raising=True)

    yield


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Per-test database session wrapped in a rolled-back transaction (R13.3).

    Each test runs inside an outer transaction on a single connection. The session
    (and any service/worker that opens its own ``SessionLocal()`` during the test)
    joins that transaction with ``join_transaction_mode="create_savepoint"``, so
    inner ``commit()`` calls land on SAVEPOINTs instead of the real transaction.
    At teardown the outer transaction is rolled back, discarding everything the test
    wrote. This isolates committed rows between tests regardless of execution order.
    """
    connection = engine.connect()
    transaction = connection.begin()

    # Bind the shared sessionmaker to this connection for the duration of the test so
    # that direct SessionLocal() callers (services, Celery tasks) join the same
    # transaction and are rolled back together.
    db_session.SessionLocal.configure(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    session = db_session.SessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Restore the session-wide engine binding for any code that runs between tests.
        db_session.SessionLocal.configure(bind=engine, join_transaction_mode="conditional_savepoint")
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
