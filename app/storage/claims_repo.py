"""CRUD repository for Claim objects backed by SQLite."""

from __future__ import annotations

from sqlmodel import Session, select

from app.models.claim import Claim, ClaimStatus
from app.storage.db import ClaimRow, get_engine


def _to_row(claim: Claim) -> ClaimRow:
    return ClaimRow(
        claim_id=claim.claim_id,
        status=claim.status.value,
        created_at=claim.created_at,
        farmer_phone=claim.farmer.phone,
        farmer_name=claim.farmer.name,
        farmer_language=claim.farmer.language,
        crop_type=claim.crop_type,
        estimated_loss_usd=claim.estimated_loss_usd,
        payload=claim.model_dump_json(),
    )


def _from_row(row: ClaimRow) -> Claim:
    claim = Claim.model_validate_json(row.payload)
    return claim


def save(claim: Claim, *, pdf_path: str | None = None) -> None:
    row = _to_row(claim)
    if pdf_path:
        row.pdf_path = pdf_path
    with Session(get_engine()) as session:
        existing = session.get(ClaimRow, claim.claim_id)
        if existing:
            existing.status = row.status
            existing.estimated_loss_usd = row.estimated_loss_usd
            existing.payload = row.payload
            if pdf_path:
                existing.pdf_path = pdf_path
            session.add(existing)
        else:
            session.add(row)
        session.commit()


def get(claim_id: str) -> Claim | None:
    with Session(get_engine()) as session:
        row = session.get(ClaimRow, claim_id)
        return _from_row(row) if row else None


def get_row(claim_id: str) -> ClaimRow | None:
    with Session(get_engine()) as session:
        return session.get(ClaimRow, claim_id)


def list_by_status(status: ClaimStatus | None = None) -> list[ClaimRow]:
    with Session(get_engine()) as session:
        stmt = select(ClaimRow).order_by(ClaimRow.created_at.desc())
        if status is not None:
            stmt = stmt.where(ClaimRow.status == status.value)
        return list(session.exec(stmt).all())


def update_status(
    claim_id: str,
    status: ClaimStatus,
    *,
    adjuster_notes: str | None = None,
    insurer_claim_id: str | None = None,
) -> Claim | None:
    claim = get(claim_id)
    if not claim:
        return None
    claim.status = status
    if adjuster_notes is not None:
        claim.adjuster_notes = adjuster_notes
    with Session(get_engine()) as session:
        row = session.get(ClaimRow, claim_id)
        if row is None:
            return None
        row.status = status.value
        row.payload = claim.model_dump_json()
        if insurer_claim_id:
            row.insurer_claim_id = insurer_claim_id
        session.add(row)
        session.commit()
    return claim
