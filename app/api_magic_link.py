"""Magic-link sign-in (passwordless).

Two endpoints:
- POST /auth/magic-link  → issues a one-time signed link emailed to the
                          user; always returns 200 to avoid enumeration.
- GET  /auth/magic-link/consume?token=…  → redeems the token, sets the
                          session cookie, redirects to /dashboard.

Token TTL is short (15 minutes) and single-use. Stored alongside the
existing one-time-token table.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr

from app import workers
from app.auth import tokens
from app.auth.routes import SESSION_COOKIE, _set_session_cookie
from app.auth.tokens import OneTimeTokenRow, _now
from app.clients import notifications
from app.config import get_settings
from app.storage import users_repo
from app.storage.audit_log import record as audit
from sqlmodel import Session, SQLModel

from app.storage.db import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/magic-link", tags=["auth"])

MAGIC_LINK_TTL = timedelta(minutes=15)


class RequestPayload(BaseModel):
    email: EmailStr


def _issue_magic_link_token(user_id: str) -> str:
    """Create a magic-link OTT directly (different ttl from the others)."""
    import secrets

    SQLModel.metadata.create_all(get_engine())
    token = f"mlnk_{secrets.token_urlsafe(32)}"
    row = OneTimeTokenRow(
        token=token,
        user_id=user_id,
        purpose="magic_link",
        expires_at=_now() + MAGIC_LINK_TTL,
    )
    with Session(get_engine()) as s:
        s.add(row)
        s.commit()
    return token


@router.post("")
def request_magic_link(payload: RequestPayload) -> dict:
    """Always returns 200 so attackers can't enumerate registered emails."""
    row = users_repo.get_by_email(payload.email)
    if row is not None:
        token = _issue_magic_link_token(row.user_id)
        base = get_settings().public_base_url.rstrip("/")
        # Send off the request path — the user only needs the 200 ack.
        workers.submit(
            notifications.send_email,
            to=row.email,
            subject="Your ClaimFarm sign-in link",
            body=(
                f"Click to sign in (expires in 15 minutes):\n"
                f"{base}/auth/magic-link/consume?token={token}\n\n"
                "If you did not request this, ignore the message."
            ),
        )
        audit(actor=row.user_id, action="auth.magic_link_requested")
    return {"ok": True}


@router.get("/consume")
def consume_magic_link(token: str, request: Request, response: Response) -> dict:
    """Single-use. Sets a fresh session cookie + redirects to /dashboard."""
    with Session(get_engine()) as s:
        row = s.get(OneTimeTokenRow, token)
        if row is None or row.purpose != "magic_link":
            raise HTTPException(status_code=400, detail="invalid token")
        if row.consumed_at is not None or row.expires_at < _now():
            raise HTTPException(status_code=400, detail="token expired or used")
        row.consumed_at = _now()
        s.add(row)
        s.commit()
        user_id = row.user_id

    user = users_repo.get(user_id)
    if user is None or user.disabled:
        raise HTTPException(status_code=404, detail="user not found")
    # Magic-link traffic also counts as proof of inbox ownership — verify.
    if not user.email_verified:
        user.email_verified = True
        users_repo.upsert(user)

    session_token = tokens.create_session(
        user_id,
        user_agent=request.headers.get("user-agent", "")[:255],
        ip=request.client.host if request.client else "",
    )
    _set_session_cookie(response, session_token)
    audit(actor=user_id, action="auth.magic_link_consumed")
    return {"ok": True, "user_id": user_id}
