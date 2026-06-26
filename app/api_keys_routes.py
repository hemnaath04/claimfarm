"""HTTP surface for managing API keys."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.storage import api_keys, users_repo
from app.storage.audit_log import record as audit

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class IssuePayload(BaseModel):
    name: str = ""
    scope: str = "claims:read"
    expires_at: Optional[datetime] = None


def _require_user(request: Request) -> tuple[str, str]:
    """Returns (user_id, org_id) for the signed-in user."""
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user_id, (row.org_id or row.user_id)  # fall back to user_id for solo accounts


@router.post("", status_code=201)
def issue_key(payload: IssuePayload, request: Request) -> dict:
    user_id, org_id = _require_user(request)
    row, secret = api_keys.issue(
        org_id=org_id,
        created_by_user_id=user_id,
        name=payload.name,
        scope=payload.scope,
        expires_at=payload.expires_at,
    )
    audit(actor=user_id, action="api_key.issued", target=row.key_id, metadata={"scope": row.scope})
    # IMPORTANT: this is the only call where the plaintext secret is returned.
    return {
        "key_id": row.key_id,
        "name": row.name,
        "scope": row.scope,
        "secret": secret,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


@router.get("")
def list_keys(request: Request) -> dict:
    _, org_id = _require_user(request)
    rows = api_keys.list_for_org(org_id)
    return {
        "items": [
            {
                "key_id": r.key_id,
                "name": r.name,
                "scope": r.scope,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
            }
            for r in rows
        ]
    }


@router.delete("/{key_id}")
def revoke_key(key_id: str, request: Request) -> dict:
    user_id, _ = _require_user(request)
    if not api_keys.revoke(key_id):
        raise HTTPException(status_code=404, detail="key not found")
    audit(actor=user_id, action="api_key.revoked", target=key_id)
    return {"ok": True}
