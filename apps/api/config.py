from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET = "change-me-in-production"
_API_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _API_ROOT.parents[1] if len(_API_ROOT.parents) > 1 else _API_ROOT


class Settings(BaseSettings):
    # Database — defaults to SQLite so it works locally with zero setup
    # Switch to postgresql://user:pass@host/db for production
    DATABASE_URL: str = "sqlite:///./iterra.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

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

    # Google OAuth (login + YouTube)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    GOOGLE_DRIVE_REDIRECT_URI: str = "http://localhost:8000/api/v1/social/callback/google-drive"

    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = ""
    LINKEDIN_SESSION_COOKIE: str = ""

    # Twitter / X OAuth 2.0 (PKCE)
    TWITTER_CLIENT_ID: str = ""
    TWITTER_CLIENT_SECRET: str = ""
    TWITTER_REDIRECT_URI: str = "http://localhost:8000/api/v1/connect/twitter/callback"

    # Instagram (Meta) OAuth
    INSTAGRAM_APP_ID: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:8000/api/v1/connect/instagram/callback"

    FRONTEND_URL: str = "http://localhost:3000"
    WAITLIST_TOTAL_SEATS: int = 100
    ADMIN_EMAILS: List[str] = []

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    MAIL_FROM: str = ""
    REPLY_TO_EMAIL: str = ""

    # Supabase
    SUPABASE_JWT_SECRET: str = ""
    SUPABASE_URL: str = ""
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = ""

    # AI
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    USE_ITERRA_AI_CALENDAR: bool = False

    # App
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _API_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
