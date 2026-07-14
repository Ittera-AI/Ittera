"""One-time connect-token store — keeps the Supabase JWT out of OAuth start URLs.

The social-connect popup is opened with a GET request to ``/connect/{platform}/start``.
Previously the caller's Supabase access token was passed as a ``?token=`` query
param, which leaks a bearer credential into browser history, server access logs,
and the ``Referer`` header.

Instead, the authenticated frontend first calls ``POST /connect/session`` (Bearer
auth) to mint a short-lived, single-use opaque token bound to its user id. That
opaque token is the only thing placed in the start URL; the start endpoint
atomically consumes it to recover the user id. A leaked one-time token is useless
after first use and expires within seconds.

Reuses ``settings.REDIS_URL``; no new environment variables are introduced.
"""

import secrets

import redis

from app.config import settings

# Time-to-live for a minted connect token: 2 minutes (popup-open + redirect).
CONNECT_TOKEN_TTL_SECONDS = 120

_KEY = "connect:onetime:{token}"


class ConnectTokenStoreError(Exception):
    """Raised when the connect-token store cannot be reached.

    Distinct from a missing/expired/already-used token, which is signalled by
    ``take_connect_token`` returning ``None``.
    """


_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def mint_connect_token(user_id: str) -> str:
    """Create and store a single-use token bound to ``user_id`` (TTL 2m).

    Returns the opaque token. Raises ``ConnectTokenStoreError`` if the store
    cannot be reached.
    """
    token = secrets.token_urlsafe(32)
    try:
        _redis().set(_KEY.format(token=token), user_id, ex=CONNECT_TOKEN_TTL_SECONDS)
    except redis.RedisError as exc:
        raise ConnectTokenStoreError(str(exc)) from exc
    return token


def take_connect_token(token: str) -> str | None:
    """Atomically fetch and delete the user id for ``token`` (single use).

    Returns the bound user id, or ``None`` if the token is absent/expired/used.
    Raises ``ConnectTokenStoreError`` if the store cannot be reached.
    """
    if not token:
        return None
    try:
        key = _KEY.format(token=token)
        pipe = _redis().pipeline()
        pipe.get(key)
        pipe.delete(key)
        value, _ = pipe.execute()
        return value
    except redis.RedisError as exc:
        raise ConnectTokenStoreError(str(exc)) from exc
