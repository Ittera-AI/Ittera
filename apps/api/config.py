from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET = "change-me-in-production"

# Resolve env files by absolute path so they load no matter the working directory
# (uvicorn is typically launched from apps/api, but the env files live at the repo root).
# config.py lives at <root>/apps/api/config.py → parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_DIR = Path(__file__).resolve().parent
# Later files override earlier ones; the user's real config is the root .env.local.
_ENV_FILES = (
    _REPO_ROOT / ".env",
    _API_DIR / ".env",
    _API_DIR / ".env.local",
    _REPO_ROOT / ".env.local",
)


class Settings(BaseSettings):
    # Database — defaults to SQLite so it works locally with zero setup
    # Switch to postgresql://user:pass@host/db for production
    DATABASE_URL: str = "sqlite:///./iterra.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    MEDIA_STORAGE_DIR: str = "uploads"
    MEDIA_PUBLIC_URL_PREFIX: str = "/api/v1/content/media-file"
    MEDIA_MAX_BYTES: int = 5 * 1024 * 1024

    # Auth
    SECRET_KEY: str = _INSECURE_SECRET

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_changed(cls, v: str) -> str:
        import os
        if v == _INSECURE_SECRET and os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError(
                "SECRET_KEY must be set to a secure random value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = ""
    # Google Drive OAuth (separate redirect from Google auth login)
    GOOGLE_DRIVE_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/google-drive"
    # LinkedIn scraper session cookie (alternative to username/password)
    LINKEDIN_SESSION_COOKIE: str = ""
    ENABLE_LINKEDIN_SYNC: bool = False
    # Twitter / X OAuth 2.0 (PKCE)
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://localhost:8000/api/v1/connect/twitter/callback"
    # Instagram (Meta) OAuth
    INSTAGRAM_APP_ID: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:8000/api/v1/connect/instagram/callback"
    # Admin access — comma-separated list of emails that can use /admin/ endpoints
    ADMIN_EMAILS: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    WAITLIST_TOTAL_SEATS: int = 100
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    MAIL_FROM: str = ""
    REPLY_TO_EMAIL: str = ""

    # Supabase — used by the backend to verify Supabase-issued JWTs
    # Find this in: Supabase Dashboard → Project Settings → API → JWT Settings → JWT Secret
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_URL: str = ""
    NEXT_PUBLIC_SUPABASE_URL: str = ""
    # Public Supabase API key used when validating a user JWT through Supabase Auth.
    # `NEXT_PUBLIC_SUPABASE_ANON_KEY` is accepted so Docker can share the web env file.
    SUPABASE_ANON_KEY: str = ""
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = ""

    # AI
    AIML_API_KEY: str = ""
    AIML_BASE_URL: str = "https://api.aimlapi.com/v1"
    AIML_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: str = "aiml"
    LLM_MODEL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    # When true and an AI provider key is configured, calendar generation uses CalendarEngine (LLM).
    # Otherwise the API returns a deterministic mock plan for demos and offline tests.
    USE_ITERRA_AI_CALENDAR: bool = False

    # App
    ENVIRONMENT: str = "development"
    # Include 127.0.0.1 — browsers treat it as a different origin than localhost.
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in _ENV_FILES),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
