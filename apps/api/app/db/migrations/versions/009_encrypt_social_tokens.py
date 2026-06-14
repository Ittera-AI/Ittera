"""Encrypt existing plaintext social_connections OAuth tokens

Revision ID: 009_encrypt_social_tokens
Revises: 008_publishing_hardening
Create Date: 2026-06-05 00:00:00.000000

This is an idempotent data migration. It walks every row in
``social_connections`` and encrypts tokens that are still stored as
plaintext, matching the application write-path behavior introduced in this
spec (tokens are encrypted only for rows that carry a refresh token — the X
confidential-client flow — so reads stay symmetric with writes).

Idempotence: each value is probed with ``_looks_like_plaintext``. A Fernet
ciphertext decrypts cleanly, so an already-encrypted value yields a non-empty
plaintext and is skipped; a raw plaintext value fails to decrypt
(``decrypt_value`` returns ``""``) and is therefore encrypted in place.
Running the migration twice never double-encrypts.

Downgrade is intentionally a no-op: encryption is not safely reversible here
because, once encrypted, we can no longer tell which rows were originally
plaintext versus which were written encrypted by the application. Decrypting
indiscriminately would corrupt rows the app expects to be ciphertext, so the
safe choice is to leave the data untouched on downgrade.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.security import decrypt_value, encrypt_value


revision: str = "009_encrypt_social_tokens"
down_revision: Union[str, None] = "008_publishing_hardening"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _looks_like_plaintext(raw: object) -> bool:
    """Return True when ``raw`` is a non-empty value that fails to decrypt.

    ``decrypt_value`` returns "" on any decryption failure. A real Fernet
    ciphertext decrypts to a non-empty string, so a non-empty value that
    decrypts to "" must be raw plaintext that was never encrypted.
    """
    if not raw:
        return False
    return decrypt_value(str(raw)) == ""


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, access_token, refresh_token FROM social_connections"
        )
    ).fetchall()

    for row in rows:
        access_token = row.access_token
        refresh_token = row.refresh_token

        # Mirror the write path: only rows that carry a refresh token are
        # expected to be encrypted at rest. Skip rows without a refresh token
        # so reads (which only decrypt when a refresh token is present) stay
        # symmetric.
        if not refresh_token:
            continue

        updates: dict[str, str] = {}
        if _looks_like_plaintext(access_token):
            updates["access_token"] = encrypt_value(str(access_token))
        if _looks_like_plaintext(refresh_token):
            updates["refresh_token"] = encrypt_value(str(refresh_token))

        if not updates:
            continue

        set_clause = ", ".join(f"{column} = :{column}" for column in updates)
        bind.execute(
            sa.text(
                f"UPDATE social_connections SET {set_clause} WHERE id = :id"
            ),
            {**updates, "id": row.id},
        )


def downgrade() -> None:
    # No-op: see module docstring. Encryption is not safely reversible because
    # we cannot distinguish rows that were originally plaintext from rows the
    # application wrote as ciphertext.
    pass
