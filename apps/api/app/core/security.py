"""
Fernet symmetric encryption for sensitive values stored in the database.

Encryption prefers a dedicated ``settings.TOKEN_ENCRYPTION_KEY`` so OAuth tokens
are not protected by the same secret that signs JWTs (``SECRET_KEY``). For
backward compatibility, decryption also accepts values that were encrypted with
the legacy SECRET_KEY-derived key via :class:`MultiFernet`, so rotating to a
dedicated key does not invalidate already-stored ciphertext.

Used for OAuth access/refresh tokens and LinkedIn credentials stored on
SocialConnection.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, MultiFernet

from app.config import settings


class TokenDecryptionError(Exception):
    """Raised when a stored token value cannot be decrypted."""


def _fernet_from(secret: str) -> Fernet:
    """Derive a Fernet instance from an arbitrary secret string via SHA-256."""
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def _multifernet() -> MultiFernet:
    """Build the MultiFernet used for encrypt/decrypt.

    The first key is the encryption key (dedicated ``TOKEN_ENCRYPTION_KEY`` when
    configured, otherwise the legacy ``SECRET_KEY``-derived key). The legacy
    ``SECRET_KEY``-derived key is always appended so values encrypted before a
    dedicated key existed still decrypt.
    """
    fernets: list[Fernet] = []
    token_key = (getattr(settings, "TOKEN_ENCRYPTION_KEY", "") or "").strip()
    if token_key:
        fernets.append(_fernet_from(token_key))
    fernets.append(_fernet_from(settings.SECRET_KEY))
    return MultiFernet(fernets)


def encrypt_value(value: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext string."""
    return _multifernet().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """
    Decrypt a previously encrypted value.
    Returns empty string on any failure (wrong key, corrupted data, etc.).
    """
    try:
        return _multifernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return ""


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt a stored OAuth token before use in an API call.

    Unlike decrypt_value, which returns "" on any failure, this raises
    TokenDecryptionError when a non-empty stored value cannot be decrypted,
    so callers can flag the connection as requiring reconnection rather than
    using an unusable token.
    """
    plaintext = decrypt_value(encrypted)
    if plaintext == "" and encrypted != "":
        raise TokenDecryptionError("stored token could not be decrypted")
    return plaintext


def decrypt_token_lenient(stored: str) -> str:
    """Return a usable token, tolerating both encrypted and legacy-plaintext values.

    While migrating LinkedIn/Instagram connections to encryption-at-rest, some
    rows may still hold plaintext tokens written before the change. A value that
    decrypts is returned as plaintext; a value that does not decrypt is assumed to
    be a legacy plaintext token (or sentinel like ``mock-linkedin-token``) and is
    returned unchanged. New rows are always encrypted, so this collapses to a
    normal decrypt once the migration window passes.
    """
    if not stored:
        return ""
    plaintext = decrypt_value(stored)
    if plaintext != "":
        return plaintext
    return stored
