import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import app.db.session as db_session
from app.db.base import Base
from app.dependencies.db import get_db
from main import app

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


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
