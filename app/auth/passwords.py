"""Password hashing helpers.

Uses PBKDF2-HMAC-SHA256 from the stdlib so we don't take on a hard
dependency until Argon2id is wired in. Production deployments should
swap to Argon2id (`argon2-cffi`) and rehash on next login.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

# 600,000 iterations (PBKDF2-SHA256) ≈ OWASP 2023 recommendation.
_ITERATIONS = 600_000
_SALT_BYTES = 16
_KEY_BYTES = 32


def hash_password(plain: str) -> str:
    """Return a compact 'algo$iter$salt$hash' string."""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, _ITERATIONS, _KEY_BYTES)
    return (
        f"pbkdf2-sha256${_ITERATIONS}${base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(digest).decode()}"
    )


def verify_password(plain: str, encoded: str) -> bool:
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
