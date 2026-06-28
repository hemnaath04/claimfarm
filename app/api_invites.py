"""Invite API: owner-only issuance, listing, and revocation of invitations.

Access to ClaimFarm is invite-only. An owner mints an invite for a staff role
(admin / moderator / reviewer — never owner or farmer); the invitee redeems it
via /auth/accept-invite to set their password. Open sign-up is disabled once
the first owner exists (see app/auth/routes.py).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app import workers
from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.clients import notifications
from app.config import get_settings
from app.models.user import UserRole
from app.storage import invites_repo, users_repo
from app.storage.audit_log import record as audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["invites"])

# Roles an owner may invite into. Owner and farmer are deliberately excluded:
# owner is reserved (privilege-escalation guard) and farmer is the end-user
# bot persona, not a console seat.
INVITABLE_ROLES = {
    UserRole.admin.value,
    UserRole.moderator.value,
    UserRole.reviewer.value,
}


class CreateInvitePayload(BaseModel):
    email: str | None = None
    role: str = UserRole.reviewer.value


def _require_owner(request: Request) -> str:
    """Returns the owner's user_id; raises 401/403/404 otherwise."""
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    if row.role != UserRole.owner.value:
        raise HTTPException(status_code=403, detail="owner role required")
    return user_id


def _status(row) -> str:
    if row.used_at is not None:
        return "used"
    if not invites_repo.is_valid(row):
        return "expired"
    return "active"


@router.post("/invites")
def create_invite(payload: CreateInvitePayload, request: Request) -> dict:
    actor = _require_owner(request)
    if payload.role not in INVITABLE_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"role must be one of {sorted(INVITABLE_ROLES)}",
        )

    invite = invites_repo.create(
        email=payload.email or "",
        role=payload.role,
        created_by=actor,
    )

    settings = get_settings()
    accept_url = f"{settings.frontend_base_url.rstrip('/')}/auth/accept?invite={invite.token}"

    if payload.email:
        actor_row = users_repo.get(actor)
        inviter = (actor_row.name or actor_row.email) if actor_row else ""
        workers.submit(
            notifications.send_invite_email,
            to=payload.email,
            inviter=inviter,
            role=payload.role,
            url=accept_url,
        )

    audit(
        actor=actor,
        action="admin.invite_created",
        target=invite.invite_id,
        metadata={"role": payload.role, "emailed": bool(payload.email)},
    )

    return {
        "invite": {
            "invite_id": invite.invite_id,
            "email": invite.email,
            "role": invite.role,
            "expires_at": invite.expires_at.isoformat(),
            "used": False,
            "accept_url": accept_url,
        },
        "accept_url": accept_url,
    }


@router.get("/invites")
def list_invites(request: Request) -> dict:
    _require_owner(request)
    rows = invites_repo.list_all()
    return {
        "items": [
            {
                "invite_id": r.invite_id,
                "email": r.email,
                "role": r.role,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat(),
                "used_at": r.used_at.isoformat() if r.used_at else None,
                "status": _status(r),
            }
            for r in rows
        ]
    }


@router.post("/invites/{invite_id}/revoke")
def revoke_invite(invite_id: str, request: Request) -> dict:
    actor = _require_owner(request)
    ok = invites_repo.revoke(invite_id)
    if not ok:
        raise HTTPException(status_code=404, detail="invite not found")
    audit(actor=actor, action="admin.invite_revoked", target=invite_id)
    return {"ok": True}
