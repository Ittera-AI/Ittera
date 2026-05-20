"""
Fernet symmetric encryption for sensitive values stored in the database.

Derives the encryption key from settings.SECRET_KEY via SHA-256 so no
separate key management is required. Used for LinkedIn credentials stored
in SocialConnection.metadata.
"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """Derives a 32-byte Fernet key from SECRET_KEY via SHA-256."""
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_value(value: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext string."""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    """
    Decrypt a previously encrypted value.
    Returns empty string on any failure (wrong key, corrupted data, etc.).
    """
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except Exception:
        return ""
