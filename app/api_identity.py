"""Identity-verification API.

Flow:
1. Authenticated user POSTs /api/identity/start → we open a session with
   the configured provider (MockProvider by default), persist the
   session id, and return the hosted URL the front-end opens in a
   modal/iframe.
2. After the user completes the provider's flow, the provider redirects
   back to /auth/verify-identity?session=…  OR  POSTs the result to our
   webhook /api/identity/webhook (production).
3. /api/identity/{session}/result returns the cached IdvResult.

Until real provider credentials are configured the MockProvider returns
deterministic results keyed by session_id.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.clients.identity_verification import IdvDecision, get_provider
from app.config import get_settings
from app.models.user import IdentityStatus
from app.storage import users_repo
from app.storage.audit_log import record as audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/identity", tags=["identity"])

# Sessions live in a JSON file for hackathon scope; production swaps to
# SQLite/Tablestore. Each row is {session_id, user_id, started_at, result?}.
SESSION_STORE = Path("/tmp/claimfarm_idv_sessions.json")


def _load_sessions() -> dict[str, dict]:
    if not SESSION_STORE.exists():
        return {}
    try:
        return json.loads(SESSION_STORE.read_text())
    except Exception:
        return {}


def _save_sessions(data: dict[str, dict]) -> None:
    SESSION_STORE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_STORE.write_text(json.dumps(data, indent=2, default=str))


def _require_user(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user_id


@router.post("/start")
def start_verification(request: Request) -> dict:
    user_id = _require_user(request)
    settings = get_settings()
    provider = get_provider()
    return_url = f"{settings.public_base_url.rstrip('/')}/auth/identity-callback"
    session = provider.start_session(user_id=user_id, return_url=return_url)

    store = _load_sessions()
    store[session["session_id"]] = {
        "user_id": user_id,
        "provider": session["provider"],
        "started_at": datetime.utcnow().isoformat() + "Z",
        "result": None,
    }
    _save_sessions(store)

    # Mark the user as IDV pending so the dashboard can show "verification in progress"
    row = users_repo.get(user_id)
    if row is not None:
        row.identity_status = IdentityStatus.pending.value
        users_repo.upsert(row)

    audit(
        actor=user_id,
        action="identity.session_started",
        target=session["session_id"],
        metadata={"provider": session["provider"]},
    )
    return session


@router.get("/{session_id}/result")
def get_verification_result(session_id: str, request: Request) -> dict:
    user_id = _require_user(request)
    store = _load_sessions()
    record_row = store.get(session_id)
    if record_row is None or record_row.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="session not found")

    if record_row.get("result") is None:
        provider = get_provider()
        result = provider.evaluate(session_id=session_id)
        record_row["result"] = {
            "decision": result.decision.value,
            "score": result.score,
            "selfie_match_score": result.selfie_match_score,
            "liveness_score": result.liveness_score,
            "extracted_name": result.extracted_name,
            "extracted_dob": result.extracted_dob,
            "extracted_document_id": result.extracted_document_id,
            "document_country": result.document_country,
            "flags": result.flags,
            "provider": result.provider,
        }
        _save_sessions(store)

        # Propagate to the user row
        row = users_repo.get(user_id)
        if row is not None:
            row.identity_score = result.score
            if result.decision is IdvDecision.approved:
                row.identity_status = IdentityStatus.approved.value
            elif result.decision is IdvDecision.rejected:
                row.identity_status = IdentityStatus.rejected.value
            else:
                row.identity_status = IdentityStatus.manual_review.value
            users_repo.upsert(row)

        audit(
            actor=user_id,
            action="identity.evaluated",
            target=session_id,
            metadata={"decision": result.decision.value, "score": result.score},
        )
    return record_row["result"]
