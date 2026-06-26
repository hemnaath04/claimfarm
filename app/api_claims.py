"""JSON API used by the Next.js adjuster dashboard.

Read-only endpoints expose Claim/queue/similar/fraud data; the
decision endpoint mutates state via the same `claims_repo` and
mock-insurer paths the Streamlit dashboard uses, so behavior stays
consistent across UIs.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents import fraud_check, past_claim_rag
from app.agents.multilingual import status_message
from app.clients import insurer
from app.models.claim import ClaimStatus
from app.storage import claims_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["adjuster"])


class DecisionPayload(BaseModel):
    decision: str = Field(description="One of: approve, reject, request_info")
    notes: str = ""


class SimilarClaim(BaseModel):
    claim_id: str | None
    farmer_phone: str | None = None
    crop_type: str | None = None
    damage_cause: str | None = None
    status: str | None = None
    estimated_loss_usd: float | None = None
    score: float


class FraudFlag(BaseModel):
    severity: str
    message: str
    related_claim_id: str | None = None
    similarity: float = 0.0


def _row_summary(row) -> dict[str, Any]:
    return {
        "claim_id": row.claim_id,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "farmer_name": row.farmer_name,
        "farmer_language": row.farmer_language,
        "crop_type": row.crop_type,
        "estimated_loss_usd": row.estimated_loss_usd,
    }


@router.get("/claims")
def list_claims(status: str | None = None) -> dict[str, Any]:
    status_arg: ClaimStatus | None = None
    if status and status.lower() != "all":
        try:
            status_arg = ClaimStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    rows = claims_repo.list_by_status(status_arg)
    all_rows = claims_repo.list_by_status()  # for stats
    counts = {s.value: 0 for s in ClaimStatus}
    for r in all_rows:
        counts[r.status] = counts.get(r.status, 0) + 1

    return {
        "items": [_row_summary(r) for r in rows],
        "stats": {
            "total": len(all_rows),
            "pending_review": counts.get("pending_review", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
            "submitted": counts.get("submitted", 0),
            "paid": counts.get("paid", 0),
        },
    }


@router.get("/claims/{claim_id}")
def get_claim(claim_id: str) -> dict[str, Any]:
    claim = claims_repo.get(claim_id)
    row = claims_repo.get_row(claim_id)
    if claim is None or row is None:
        raise HTTPException(status_code=404, detail="claim not found")

    similar = past_claim_rag.find_similar(claim, k=3)
    flags = fraud_check.check(claim)

    return {
        "claim": claim.model_dump(mode="json"),
        "pdf_path": row.pdf_path,
        "insurer_claim_id": row.insurer_claim_id,
        "similar": [
            {
                "claim_id": h.metadata.get("claim_id"),
                "farmer_phone": h.metadata.get("farmer_phone"),
                "crop_type": h.metadata.get("crop_type"),
                "damage_cause": h.metadata.get("damage_cause"),
                "status": h.metadata.get("status"),
                "estimated_loss_usd": h.metadata.get("estimated_loss_usd"),
                "score": h.score,
            }
            for h in similar
        ],
        "fraud_flags": [
            {
                "severity": f.severity,
                "message": f.message,
                "related_claim_id": f.related_claim_id,
                "similarity": f.similarity,
            }
            for f in flags
        ],
    }


@router.get("/claims/{claim_id}/localized_reply")
def get_localized_reply(claim_id: str) -> dict[str, str]:
    claim = claims_repo.get(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")
    try:
        return {"message": status_message(claim)}
    except Exception as exc:  # noqa: BLE001
        return {"message": "", "error": str(exc)}


@router.post("/claims/{claim_id}/decision")
def post_decision(claim_id: str, body: DecisionPayload) -> dict[str, Any]:
    claim = claims_repo.get(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="claim not found")

    if body.decision == "approve":
        claims_repo.update_status(claim_id, ClaimStatus.approved, adjuster_notes=body.notes)
        try:
            record = insurer.submit(claim)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"insurer call failed: {exc}") from exc
        terminal = record.get("status", "submitted")
        next_status = (
            ClaimStatus.approved
            if terminal == "approved"
            else ClaimStatus.rejected
            if terminal == "rejected"
            else ClaimStatus.submitted
        )
        claims_repo.update_status(
            claim_id,
            next_status,
            adjuster_notes=body.notes,
            insurer_claim_id=record.get("insurer_claim_id"),
        )
        return {"status": next_status.value, "insurer": record}

    if body.decision == "reject":
        claims_repo.update_status(claim_id, ClaimStatus.rejected, adjuster_notes=body.notes)
        return {"status": "rejected"}

    if body.decision == "request_info":
        claims_repo.update_status(
            claim_id, ClaimStatus.pending_review, adjuster_notes=body.notes
        )
        return {"status": "pending_review"}

    raise HTTPException(status_code=400, detail=f"unknown decision: {body.decision}")


def install_api(app) -> None:
    """Attach the router and CORS policy to the given FastAPI app.

    CORS is credentialed (session cookies + Bearer keys both ride on the
    same browser request), so we must enumerate exact origins — ``*`` +
    ``allow_credentials=True`` is rejected by the CORS spec. Origins come
    from ``CORS_ALLOWED_ORIGINS`` (comma-separated) with sane defaults
    covering local dev + the deployed Vercel surface.
    """
    import os as _os

    raw = _os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()
    if raw:
        origins = [o.strip() for o in raw.split(",") if o.strip()]
    else:
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://claimfarm-dashboard.vercel.app",
        ]

    app.include_router(router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # Preview deploys land on *.vercel.app subdomains; allow them all.
        allow_origin_regex=r"https://claimfarm-dashboard(-[a-z0-9-]+)?\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _no_cache_api(request, call_next):
        """Stop Cloudflare's quick-tunnel edge cache from serving stale API JSON.

        The trycloudflare.com tunnel caches GET responses by URL by default
        and uses the same cache key across all clients. Forcing no-store on
        every /api/* response keeps the Vercel dashboard in lock-step with
        the latest SQLite state.
        """
        response = await call_next(request)
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response
