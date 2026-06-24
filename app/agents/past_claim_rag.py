"""Index claims into the vector store and retrieve similar ones for adjusters."""

from __future__ import annotations

from app.clients.vector_store import QueryHit, VectorDoc, get_store
from app.models.claim import Claim

COLLECTION = "past_claims"


def _claim_to_text(claim: Claim) -> str:
    bits = [
        f"{claim.crop_type} damaged by {claim.damage.damage_cause.value}.",
        f"Severity {claim.damage.severity}/100, affected area {claim.damage.affected_area_pct}%.",
        claim.damage.notes,
        f"Visible indicators: {', '.join(claim.damage.visible_indicators)}.",
    ]
    if claim.farmer_narrative:
        bits.append(f"Farmer note: {claim.farmer_narrative}")
    return " ".join(b for b in bits if b)


def _claim_to_metadata(claim: Claim) -> dict:
    return {
        "claim_id": claim.claim_id,
        "farmer_phone": claim.farmer.phone,
        "farmer_name": claim.farmer.name,
        "crop_type": claim.crop_type,
        "damage_cause": claim.damage.damage_cause.value,
        "severity": claim.damage.severity,
        "affected_area_pct": claim.damage.affected_area_pct,
        "estimated_loss_usd": claim.estimated_loss_usd,
        "status": claim.status.value,
        "date_of_damage": claim.date_of_damage.isoformat(),
        "latitude": claim.farmer.latitude,
        "longitude": claim.farmer.longitude,
    }


def index_claim(claim: Claim) -> None:
    get_store().upsert(
        COLLECTION,
        [
            VectorDoc(
                id=claim.claim_id,
                text=_claim_to_text(claim),
                metadata=_claim_to_metadata(claim),
            )
        ],
    )


def find_similar(claim: Claim, *, k: int = 5, exclude_self: bool = True) -> list[QueryHit]:
    """Top-K most similar past claims to this one (excluding itself by default)."""
    store = get_store()
    hits = store.query(COLLECTION, _claim_to_text(claim), k=k + (1 if exclude_self else 0))
    if exclude_self:
        hits = [h for h in hits if h.metadata.get("claim_id") != claim.claim_id]
    return hits[:k]
