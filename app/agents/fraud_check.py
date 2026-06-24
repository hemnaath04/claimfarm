"""Surface possible fraud patterns by comparing a new claim against the past."""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.past_claim_rag import COLLECTION as PAST_CLAIMS
from app.agents.past_claim_rag import _claim_to_text
from app.clients.vector_store import QueryHit, get_store
from app.models.claim import Claim

DUPLICATE_THRESHOLD = 0.93
GENERIC_REUSE_THRESHOLD = 0.97  # near-identical narrative across farmers


@dataclass
class FraudFlag:
    severity: str  # "warn" | "block"
    message: str
    related_claim_id: str | None = None
    similarity: float = 0.0


def check(claim: Claim) -> list[FraudFlag]:
    """Return a list of fraud flags. Empty list means clean."""
    store = get_store()
    flags: list[FraudFlag] = []

    text = _claim_to_text(claim)

    # 1) Same farmer submitting near-duplicate claims
    same_phone = store.query(
        PAST_CLAIMS,
        text,
        k=3,
        where={"farmer_phone": claim.farmer.phone},
    )
    for h in same_phone:
        if h.metadata.get("claim_id") == claim.claim_id:
            continue
        if h.score >= DUPLICATE_THRESHOLD:
            flags.append(
                FraudFlag(
                    severity="block",
                    message=(
                        f"Near-duplicate of past claim {h.metadata.get('claim_id')} "
                        f"from the same phone (similarity {h.score:.2f})."
                    ),
                    related_claim_id=str(h.metadata.get("claim_id")),
                    similarity=h.score,
                )
            )

    # 2) Different farmer, suspiciously identical narrative
    global_matches = store.query(PAST_CLAIMS, text, k=5)
    for h in global_matches:
        if h.metadata.get("claim_id") == claim.claim_id:
            continue
        if h.metadata.get("farmer_phone") == claim.farmer.phone:
            continue
        if h.score >= GENERIC_REUSE_THRESHOLD:
            flags.append(
                FraudFlag(
                    severity="warn",
                    message=(
                        f"Wording is near-identical to claim {h.metadata.get('claim_id')} "
                        f"from a different farmer (similarity {h.score:.2f})."
                    ),
                    related_claim_id=str(h.metadata.get("claim_id")),
                    similarity=h.score,
                )
            )

    return flags


__all__ = ["FraudFlag", "check", "_score_hits"]


def _score_hits(hits: list[QueryHit]) -> list[QueryHit]:  # kept for tests
    return sorted(hits, key=lambda h: h.score, reverse=True)
