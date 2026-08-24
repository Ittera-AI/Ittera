"""Supabase identity verification and first-time provisioning contracts."""

import pytest
from fastapi import HTTPException

from app.dependencies.auth import (
    _get_or_create_user_from_supabase,
    _is_email_verified,
)
from app.models.user import User


def _payload(
    *,
    subject: str,
    email: str,
    verified: bool = True,
) -> dict:
    return {
        "sub": subject,
        "email": email,
        "email_verified": verified,
        "aud": "authenticated",
        "user_metadata": {"full_name": "Supabase User"},
    }


def test_email_verification_uses_only_authoritative_top_level_claims() -> None:
    assert _is_email_verified({"email_verified": True})
    assert _is_email_verified(
        {"email_confirmed_at": "2026-08-22T00:00:00Z"}
    )
    assert not _is_email_verified(
        {
            "email_verified": False,
            "email_confirmed_at": "2026-08-22T00:00:00Z",
            "user_metadata": {
                "email_verified": True,
                "email_confirmed_at": "2026-08-22T00:00:00Z",
            },
        }
    )
    assert not _is_email_verified(
        {"user_metadata": {"email_verified": True}}
    )
    assert not _is_email_verified({})


def test_unverified_first_time_identity_cannot_provision(db) -> None:
    payload = _payload(
        subject="unverified-supabase-id",
        email="unverified-supabase@example.com",
        verified=False,
    )

    with pytest.raises(HTTPException) as exc_info:
        _get_or_create_user_from_supabase(db, payload)

    assert exc_info.value.status_code == 401
    assert db.query(User).filter(User.id == payload["sub"]).first() is None
    assert db.query(User).filter(User.email == payload["email"]).first() is None


def test_user_metadata_cannot_link_an_existing_account(db) -> None:
    victim = User(
        id="legacy-victim-id",
        email="legacy-victim@example.com",
        hashed_password="unused",
        name="Legacy Victim",
    )
    db.add(victim)
    db.commit()

    payload = _payload(
        subject="attacker-supabase-id",
        email=victim.email,
        verified=False,
    )
    payload["user_metadata"].update(
        {
            "email_verified": True,
            "email_confirmed_at": "2026-08-22T00:00:00Z",
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        _get_or_create_user_from_supabase(db, payload)

    assert exc_info.value.status_code == 401
    assert db.query(User).filter(User.id == victim.id).one().email == victim.email
    assert db.query(User).filter(User.id == payload["sub"]).first() is None


def test_verified_first_time_identity_is_provisioned(db) -> None:
    payload = _payload(
        subject="verified-supabase-id",
        email="verified-supabase@example.com",
    )

    user = _get_or_create_user_from_supabase(db, payload)

    assert user.id == payload["sub"]
    assert user.email == payload["email"]
    assert user.name == "Supabase User"


def test_existing_subject_with_different_email_fails_closed(db) -> None:
    existing = User(
        id="existing-supabase-id",
        email="original-supabase@example.com",
        hashed_password="unused",
        name="Original User",
    )
    db.add(existing)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        _get_or_create_user_from_supabase(
            db,
            _payload(
                subject=existing.id,
                email="changed-supabase@example.com",
            ),
        )

    assert exc_info.value.status_code == 401
    assert db.query(User).filter(User.id == existing.id).one().email == existing.email


@pytest.mark.asyncio
async def test_realistic_local_supabase_jwt_uses_authoritative_user_fallback(
    db,
    monkeypatch,
) -> None:
    from unittest.mock import AsyncMock

    from fastapi.security import HTTPAuthorizationCredentials

    from app.dependencies import auth as auth_dependency

    local_payload = {
        "sub": "fallback-supabase-id",
        "email": "fallback-supabase@example.com",
        "aud": "authenticated",
        "user_metadata": {
            "full_name": "Fallback Supabase User",
            "email_verified": True,
        },
    }
    verified_payload = {
        **local_payload,
        "email_confirmed_at": "2026-08-22T00:00:00Z",
    }
    fetch_user = AsyncMock(return_value=verified_payload)
    monkeypatch.setattr(
        auth_dependency,
        "_decode_supabase_jwt",
        lambda token: local_payload,
    )
    monkeypatch.setattr(auth_dependency, "_fetch_supabase_user", fetch_user)

    user = await auth_dependency.get_current_user(
        credentials=HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="locally-valid-supabase-token",
        ),
        cookie_token=None,
        db=db,
    )

    assert user.id == local_payload["sub"]
    assert user.email == local_payload["email"]
    fetch_user.assert_awaited_once_with("locally-valid-supabase-token")
