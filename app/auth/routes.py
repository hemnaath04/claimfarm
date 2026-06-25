"""FastAPI auth router: sign-up, sign-in, sign-out, reset, verify."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.auth import passwords, tokens
from app.clients import notifications
from app.config import get_settings
from app.models.user import UserRole
from app.storage import users_repo
from app.storage.audit_log import record as audit
from app.storage.users_repo import UserRow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_COOKIE = "cf_session"


class SignUpPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""
    org: str = ""


class SignInPayload(BaseModel):
    email: EmailStr
    password: str


class ResetRequestPayload(BaseModel):
    email: EmailStr


class ConfirmResetPayload(BaseModel):
    token: str
    password: str = Field(min_length=8)


def _set_session_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        secure=s.public_base_url.startswith("https://"),
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.post("/sign-up", status_code=status.HTTP_201_CREATED)
def sign_up(payload: SignUpPayload, request: Request, response: Response) -> dict:
    existing = users_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="email already registered")

    user_id = f"usr_{int(datetime.utcnow().timestamp())}_{payload.email.split('@')[0][:8]}"
    row = UserRow(
        user_id=user_id,
        email=payload.email,
        name=payload.name,
        role=UserRole.owner.value,
        password_hash=passwords.hash_password(payload.password),
    )
    users_repo.upsert(row)

    # Issue an email-verification token and notify (logs-only when SMTP is unset)
    verify_token = tokens.issue_email_verification_token(user_id)
    settings = get_settings()
    base = settings.public_base_url.rstrip("/")
    notifications.send(
        kind="welcome",
        user_id=user_id,
        email=payload.email,
        vars={
            "name": payload.name or "there",
            "verification_url": f"{base}/auth/verify?token={verify_token}",
        },
    )

    audit(
        actor=user_id,
        action="user.sign_up",
        target=user_id,
        metadata={"email_domain": payload.email.split("@", 1)[-1]},
    )

    session_token = tokens.create_session(
        user_id, user_agent=request.headers.get("user-agent", "")[:255], ip=request.client.host if request.client else ""
    )
    _set_session_cookie(response, session_token)
    return {"user_id": user_id, "session": session_token, "verification_email_sent": True}


@router.post("/sign-in")
def sign_in(payload: SignInPayload, request: Request, response: Response) -> dict:
    row = users_repo.get_by_email(payload.email)
    if row is None or row.disabled or not row.password_hash:
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not passwords.verify_password(payload.password, row.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    users_repo.update_last_seen(row.user_id)
    session_token = tokens.create_session(
        row.user_id,
        user_agent=request.headers.get("user-agent", "")[:255],
        ip=request.client.host if request.client else "",
    )
    _set_session_cookie(response, session_token)
    audit(actor=row.user_id, action="user.sign_in")
    return {"user_id": row.user_id, "session": session_token}


@router.post("/sign-out")
def sign_out(request: Request, response: Response) -> dict:
    token = request.cookies.get(SESSION_COOKIE, "")
    tokens.delete_session(token)
    _clear_session_cookie(response)
    return {"ok": True}


@router.post("/reset")
def reset_request(payload: ResetRequestPayload) -> dict:
    """Always returns OK to avoid leaking which emails are registered."""
    row = users_repo.get_by_email(payload.email)
    if row is not None:
        token = tokens.issue_password_reset_token(row.user_id)
        base = get_settings().public_base_url.rstrip("/")
        notifications.send_email(
            to=row.email,
            subject="Reset your ClaimFarm password",
            body=f"Click this link to reset (expires in 1h):\n{base}/auth/reset/confirm?token={token}",
        )
        audit(actor=row.user_id, action="user.reset_requested")
    return {"ok": True}


@router.post("/reset/confirm")
def reset_confirm(payload: ConfirmResetPayload, response: Response) -> dict:
    user_id = tokens.redeem_password_reset_token(payload.token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.password_hash = passwords.hash_password(payload.password)
    users_repo.upsert(row)
    audit(actor=user_id, action="user.password_reset")
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/verify")
def verify_email(token: str) -> dict:
    user_id = tokens.redeem_email_verification_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="invalid or expired token")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.email_verified = True
    users_repo.upsert(row)
    audit(actor=user_id, action="user.email_verified")
    return {"ok": True, "user_id": user_id}


@router.get("/me")
def me(request: Request) -> dict:
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return {
        "user_id": row.user_id,
        "email": row.email,
        "name": row.name,
        "role": row.role,
        "email_verified": row.email_verified,
        "identity_status": row.identity_status,
        "org_id": row.org_id,
    }
