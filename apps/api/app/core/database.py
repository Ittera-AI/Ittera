"""
Re-exports SessionLocal from app.db.session for use in Celery workers.
Workers import from here so they don't need to know the internal DB module path.
"""

from app.db.session import SessionLocal  # noqa: F401
