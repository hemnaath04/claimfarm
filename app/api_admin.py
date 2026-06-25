"""Admin API: user search, suspend, audit log, manual identity review."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.models.user import UserRole
from app.storage import users_repo
from app.storage.audit_log import record as audit
from app.storage.audit_log import tail as audit_tail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    if row.role not in (UserRole.owner.value, UserRole.admin.value):
        raise HTTPException(status_code=403, detail="admin role required")
    return user_id


@router.get("/users")
def list_users(request: Request) -> dict:
    actor = _require_admin(request)
    rows = users_repo.list_all()
    return {
        "items": [
            {
                "user_id": r.user_id,
                "email": r.email,
                "name": r.name,
                "role": r.role,
                "identity_status": r.identity_status,
                "identity_score": r.identity_score,
                "email_verified": r.email_verified,
                "disabled": r.disabled,
                "last_seen_at": r.last_seen_at.isoformat() if r.last_seen_at else None,
            }
            for r in rows
        ],
        "actor": actor,
    }


@router.post("/users/{user_id}/suspend")
def suspend_user(user_id: str, request: Request) -> dict:
    actor = _require_admin(request)
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.disabled = True
    users_repo.upsert(row)
    audit(actor=actor, action="admin.user_suspended", target=user_id)
    return {"ok": True, "user_id": user_id}


@router.post("/users/{user_id}/unsuspend")
def unsuspend_user(user_id: str, request: Request) -> dict:
    actor = _require_admin(request)
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.disabled = False
    users_repo.upsert(row)
    audit(actor=actor, action="admin.user_unsuspended", target=user_id)
    return {"ok": True, "user_id": user_id}


@router.post("/users/{user_id}/role")
def set_role(user_id: str, role: str, request: Request) -> dict:
    actor = _require_admin(request)
    try:
        new_role = UserRole(role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.role = new_role.value
    users_repo.upsert(row)
    audit(actor=actor, action="admin.role_changed", target=user_id, metadata={"role": new_role.value})
    return {"ok": True}


@router.get("/audit")
def audit_log_tail(limit: int = 100, request: Request = None) -> dict:  # type: ignore[assignment]
    actor = _require_admin(request)  # type: ignore[arg-type]
    items = audit_tail(limit)
    audit(actor=actor, action="admin.audit_viewed", metadata={"limit": limit})
    return {"items": items}
