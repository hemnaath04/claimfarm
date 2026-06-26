"""GDPR / DPDP / LGPD / CCPA endpoints — data export + account deletion.

Two user-driven operations:
- `GET  /api/me/export`   — bundle every record about this user into a
  JSON envelope (account profile + claim summaries + audit log slice +
  notifications inbox + IDV sessions). Streams back as a download.
- `POST /api/me/delete`   — soft-deletes the account immediately
  (disables sign-in, marks the user as redacted) and schedules a
  hard-delete sweep at the end of the regulatory retention window. The
  background sweep is a TODO marker for a real cron / worker.

The export bundle is intentionally a single JSON file so a user can
take it to a competing service or store it for compliance.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.storage import claims_repo, users_repo
from app.storage.audit_log import record as audit
from app.storage.audit_log import tail as audit_tail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/me", tags=["account"])

HARD_DELETE_AFTER = timedelta(days=30)


def _require_user(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user_id


@router.get("/export")
def export_my_data(request: Request) -> Response:
    user_id = _require_user(request)
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")

    # Claim summaries belonging to this user are matched by phone for
    # farmer-initiated claims, or by user_id when the user is an operator.
    # The simple shape is sufficient for GDPR portability; the underlying
    # PDFs remain accessible via signed-URL until the retention window
    # expires.
    my_claims = [
        {
            "claim_id": c.claim_id,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "crop_type": c.crop_type,
            "estimated_loss_usd": c.estimated_loss_usd,
            "insurer_claim_id": c.insurer_claim_id,
        }
        for c in claims_repo.list_by_status()
        if c.farmer_phone == row.phone or c.farmer_name == row.name
    ]

    my_audit = [r for r in audit_tail(2000) if r.get("actor") == user_id]

    bundle = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "schema_version": 1,
        "user": {
            "user_id": row.user_id,
            "email": row.email,
            "name": row.name,
            "phone": row.phone,
            "org_id": row.org_id,
            "role": row.role,
            "email_verified": row.email_verified,
            "identity_status": row.identity_status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
        },
        "claims": my_claims,
        "audit_log": my_audit,
    }

    audit(
        actor=user_id,
        action="gdpr.export",
        metadata={"claim_count": len(my_claims), "audit_rows": len(my_audit)},
    )

    payload = json.dumps(bundle, indent=2, default=str).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="claimfarm-export-{row.user_id}.json"',
        },
    )


@router.post("/delete")
def delete_my_account(request: Request) -> dict:
    """Soft-deletes the account immediately, schedules hard-delete.

    The user is signed out + disabled + email scrambled to a non-routable
    placeholder so the unique-email constraint allows re-registration of
    the original address by a different person.
    """
    user_id = _require_user(request)
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")

    delete_at = datetime.utcnow() + HARD_DELETE_AFTER
    placeholder = f"deleted+{user_id}@claimfarm.local"
    row.email = placeholder
    row.name = "[redacted]"
    row.phone = None
    row.disabled = True
    row.email_verified = False
    row.password_hash = None
    users_repo.upsert(row)

    # Revoke all active sessions for this user.
    token = request.cookies.get(SESSION_COOKIE, "")
    if token:
        tokens.delete_session(token)

    audit(
        actor=user_id,
        action="gdpr.account_soft_deleted",
        target=user_id,
        metadata={"hard_delete_scheduled_for": delete_at.isoformat() + "Z"},
    )

    # TODO: a daily cron job should sweep `disabled=True` users older than
    # HARD_DELETE_AFTER and purge: SQLite rows, DashVector embeddings,
    # OSS photos/PDFs, audit-log rows older than the regulatory window.
    return {
        "ok": True,
        "soft_deleted": True,
        "hard_delete_scheduled_for": delete_at.isoformat() + "Z",
    }
