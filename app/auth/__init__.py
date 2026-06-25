"""Authentication subsystem.

- Password hashing: PBKDF2-HMAC-SHA256 (stdlib). Production should
  upgrade to Argon2id via `argon2-cffi` once that dependency is added.
- Sessions: opaque random tokens, persisted in SQLite. Each token has a
  short-lived access window (1 hour) and a long-lived refresh window
  (30 days). Cookies are HTTP-only + SameSite=lax in production.
- CSRF: double-submit cookie pattern when forms post directly.
"""

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import (
    create_session,
    delete_session,
    get_session_user,
    issue_email_verification_token,
    issue_password_reset_token,
    redeem_password_reset_token,
    redeem_email_verification_token,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_session",
    "delete_session",
    "get_session_user",
    "issue_email_verification_token",
    "issue_password_reset_token",
    "redeem_password_reset_token",
    "redeem_email_verification_token",
]
