"""Password hashing.

Default: Argon2id (OWASP 2023 recommendation), provided by argon2-cffi.
Legacy PBKDF2-SHA256 hashes from earlier accounts are still verified +
transparently rehashed to Argon2id on the next successful sign-in.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id parameters tuned for ~250ms on a modern laptop. OWASP 2023:
# m=64 MiB, t=3, p=4.
_ph = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=4, hash_len=32, salt_len=16)


def hash_password(plain: str) -> str:
    """Hash with Argon2id. Output starts with `$argon2id$…`."""
    return _ph.hash(plain)


def verify_password(plain: str, encoded: str) -> bool:
    """Verify against either Argon2id or legacy PBKDF2-SHA256 hashes."""
    if encoded.startswith("$argon2"):
        try:
            return _ph.verify(encoded, plain)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
    if encoded.startswith("pbkdf2-sha256$"):
        return _verify_pbkdf2(plain, encoded)
    return False


def needs_rehash(encoded: str) -> bool:
    """True when the stored hash should be upgraded on next successful login."""
    if not encoded.startswith("$argon2"):
        return True
    try:
        return _ph.check_needs_rehash(encoded)
    except InvalidHashError:
        return True


# --- Legacy PBKDF2 (kept for accounts created before the Argon2id upgrade) ---


def _verify_pbkdf2(plain: str, encoded: str) -> bool:
    try:
        algo, iter_str, salt_b64, hash_b64 = encoded.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2-sha256":
        return False
    try:
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except Exception:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain.encode("utf-8"), salt, iterations, len(expected)
    )
    return hmac.compare_digest(digest, expected)
