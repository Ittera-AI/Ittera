"""Single-use OAuth connect-state store — binds an OAuth ``state`` to its session.

The Twitter/X connect flow already gets a single-use, session-bound guarantee for
free: a PKCE ``code_verifier`` is stored server-side keyed by the OAuth ``state``
(see ``pkce_store``) and is atomically consumed at the callback, so a replayed or
unknown ``state`` has no verifier and is rejected.

LinkedIn and Instagram are not PKCE flows, so they have no verifier to anchor that
guarantee. This store provides the equivalent: at ``/start`` the server records the
``state`` (keyed in Redis, TTL 10m) bound to the initiating user id, and at
``/callback`` the server atomically fetches and deletes that record. A ``state``
that is missing, expired, unbound, or already used therefore resolves to ``None``
and the callback is rejected — the same single-use/binding semantics as X.

Reuses ``settings.REDIS_URL``; no new environment variables are introduced.
"""

import redis

from app.config import settings

# Time-to-live for a bound connect-state: 10 minutes, matching the ``exp`` baked
# into the signed state JWT by ``_make_connect_state``.
CONNECT_STATE_TTL_SECONDS = 600

_KEY = "connect:state:{state}"


class ConnectStateStoreError(Exception):
    """Raised when the connect-state store cannot be reached.

    Distinct from a missing/expired/unbound/already-used state, which is signalled
    by ``take_connect_state`` returning ``None``.
    """


_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def bind_connect_state(state: str, user_id: str) -> None:
    """Bind ``state`` to the initiating ``user_id`` with a 10-minute TTL.

    Raises ``ConnectStateStoreError`` if the store cannot be reached.
    """
    try:
        _redis().set(_KEY.format(state=state), user_id, ex=CONNECT_STATE_TTL_SECONDS)
    except redis.RedisError as exc:
        raise ConnectStateStoreError(str(exc)) from exc


def take_connect_state(state: str) -> str | None:
    """Atomically fetch and delete the user id bound to ``state`` (single use).

    Returns the bound user id, or ``None`` if the state is absent, expired,
    unbound, or already consumed. Raises ``ConnectStateStoreError`` if the store
    cannot be reached.
    """
    if not state:
        return None
    try:
        key = _KEY.format(state=state)
        pipe = _redis().pipeline()
        pipe.get(key)
        pipe.delete(key)
        value, _ = pipe.execute()
        return value
    except redis.RedisError as exc:
        raise ConnectStateStoreError(str(exc)) from exc
