"""
PKCE Verifier Store — durable, cross-worker storage for OAuth PKCE verifiers.

The OAuth 2.0 + PKCE connect flow generates a ``code_verifier`` at
``/twitter/start`` that must be available again at ``/twitter/callback``. In a
multi-worker deployment the two requests may land on different workers, so the
verifier is held in Redis (keyed by the OAuth ``state``) rather than in a
per-process dict.

Reuses the existing ``settings.REDIS_URL``; no new environment variables are
introduced.
"""

import redis

from app.config import settings

# Time-to-live for a stored verifier: 10 minutes.
VERIFIER_TTL_SECONDS = 600

_KEY = "pkce:verifier:{state}"


class VerifierStoreError(Exception):
    """Raised when the verifier store cannot be reached.

    This is distinct from a missing/expired verifier, which is signalled by
    ``take_verifier`` returning ``None``.
    """


_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def put_verifier(state: str, verifier: str) -> None:
    """Store ``verifier`` keyed by ``state`` with a 10-minute TTL.

    Raises ``VerifierStoreError`` if the store cannot be reached.
    """
    try:
        _redis().set(_KEY.format(state=state), verifier, ex=VERIFIER_TTL_SECONDS)
    except redis.RedisError as exc:
        raise VerifierStoreError(str(exc)) from exc


def take_verifier(state: str) -> str | None:
    """Atomically fetch and delete the verifier for ``state``.

    Returns the stored verifier, or ``None`` if it is absent or expired.
    Raises ``VerifierStoreError`` if the store cannot be reached.
    """
    try:
        key = _KEY.format(state=state)
        pipe = _redis().pipeline()
        pipe.get(key)
        pipe.delete(key)
        value, _ = pipe.execute()
        return value
    except redis.RedisError as exc:
        raise VerifierStoreError(str(exc)) from exc
