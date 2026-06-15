"""Stand-in InsurerCo REST API.

Simulates a downstream crop-insurance carrier. Stores claims in memory and
transitions them through realistic stages with a small probability of
non-approval. Good enough for the hackathon demo, not a substitute for an
actual integration.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


class InsurerStatus(str, Enum):
    received = "received"
    under_review = "under_review"
    approved = "approved"
    needs_more_info = "needs_more_info"
    rejected = "rejected"
    paid = "paid"


class ClaimSubmission(BaseModel):
    """Inbound from ClaimFarm — the only fields the insurer needs to file."""

    external_claim_id: str = Field(description="ClaimFarm-side claim id, e.g. CF-ABC123")
    farmer_name: str
    farmer_phone: str
    crop_type: str
    damage_cause: str
    severity: int = Field(ge=0, le=100)
    affected_area_pct: int = Field(ge=0, le=100)
    farm_area_hectares: float
    requested_payout_usd: float
    date_of_damage: str
    pdf_url: str | None = None


class ClaimRecord(BaseModel):
    insurer_claim_id: str
    external_claim_id: str
    status: InsurerStatus
    submitted_at: datetime
    decided_at: datetime | None = None
    approved_payout_usd: float | None = None
    expected_payout_date: str | None = None
    reviewer_notes: str = ""


app = FastAPI(title="InsurerCo (mock)", version="0.1.0")

_db: dict[str, ClaimRecord] = {}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "insurerco-mock"}


@app.post("/claims", response_model=ClaimRecord, status_code=201)
def submit_claim(submission: ClaimSubmission) -> ClaimRecord:
    insurer_id = f"INS-{uuid4().hex[:8].upper()}"
    record = ClaimRecord(
        insurer_claim_id=insurer_id,
        external_claim_id=submission.external_claim_id,
        status=InsurerStatus.received,
        submitted_at=datetime.utcnow(),
    )
    _db[insurer_id] = record
    _decide(record, submission)
    return record


@app.get("/claims/{insurer_claim_id}", response_model=ClaimRecord)
def get_claim(insurer_claim_id: str) -> ClaimRecord:
    record = _db.get(insurer_claim_id)
    if record is None:
        raise HTTPException(status_code=404, detail="claim not found")
    return record


@app.get("/claims", response_model=list[ClaimRecord])
def list_claims() -> list[ClaimRecord]:
    return list(_db.values())


def _decide(record: ClaimRecord, submission: ClaimSubmission) -> None:
    """Synchronously transition a freshly received claim to a terminal status.

    Real insurers are async; for demo purposes we settle immediately so the
    operator dashboard reflects an outcome on the same request.
    """
    record.status = InsurerStatus.under_review

    # Probabilistic outcome biased by corroboration strength heuristics:
    # implausibly large payouts get scrutinized more.
    base_approve = 0.78
    if submission.requested_payout_usd > 5000:
        base_approve -= 0.2
    if submission.severity < 25:
        base_approve -= 0.3
    base_approve = max(0.1, min(0.95, base_approve))

    roll = random.random()
    if roll < base_approve:
        record.status = InsurerStatus.approved
        haircut = random.uniform(0.85, 1.0)
        record.approved_payout_usd = round(submission.requested_payout_usd * haircut, 2)
        record.expected_payout_date = (
            datetime.utcnow() + timedelta(days=random.randint(7, 21))
        ).date().isoformat()
        record.reviewer_notes = "Auto-approved based on submitted evidence."
    elif roll < base_approve + 0.15:
        record.status = InsurerStatus.needs_more_info
        record.reviewer_notes = "Additional photos and a witness statement requested."
    else:
        record.status = InsurerStatus.rejected
        record.reviewer_notes = "Damage cause could not be substantiated."

    record.decided_at = datetime.utcnow()
