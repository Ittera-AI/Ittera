import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

_SQLITE_FALLBACK = "sqlite:///./iterra.db"


def _resolve_database_url() -> str:
    url = settings.DATABASE_URL
    if settings.ENVIRONMENT != "development" or url.startswith("sqlite"):
        return url
    if "postgres" not in url:
        return url

    try:
        probe = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
        probe.dispose()
        return url
    except Exception as exc:
        logger.warning(
            "PostgreSQL unavailable in development (%s). Using SQLite fallback at %s.",
            exc,
            _SQLITE_FALLBACK,
        )
        return _SQLITE_FALLBACK


DATABASE_URL = _resolve_database_url()
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {"connect_timeout": 10},
    **({} if _is_sqlite else {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
