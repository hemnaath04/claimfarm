"""Client for the (mock) InsurerCo REST API."""

from __future__ import annotations

import os

import httpx

from app.models.claim import Claim

INSURER_BASE_URL = os.environ.get("INSURER_BASE_URL", "http://localhost:8001")


def _submission_payload(claim: Claim, pdf_url: str | None = None) -> dict:
    return {
        "external_claim_id": claim.claim_id,
        "farmer_name": claim.farmer.name,
        "farmer_phone": claim.farmer.phone,
        "crop_type": claim.crop_type,
        "damage_cause": claim.damage.damage_cause.value,
        "severity": claim.damage.severity,
        "affected_area_pct": claim.damage.affected_area_pct,
        "farm_area_hectares": claim.farmer.farm_area_hectares,
        "requested_payout_usd": claim.estimated_loss_usd,
        "date_of_damage": claim.date_of_damage.isoformat(),
        "pdf_url": pdf_url,
    }


def submit(claim: Claim, *, pdf_url: str | None = None, base_url: str | None = None) -> dict:
    """Submit a claim to the insurer and return its decision record."""
    url = (base_url or INSURER_BASE_URL).rstrip("/") + "/claims"
    r = httpx.post(url, json=_submission_payload(claim, pdf_url), timeout=15.0)
    r.raise_for_status()
    return r.json()


def get(insurer_claim_id: str, *, base_url: str | None = None) -> dict:
    url = (base_url or INSURER_BASE_URL).rstrip("/") + f"/claims/{insurer_claim_id}"
    r = httpx.get(url, timeout=15.0)
    r.raise_for_status()
    return r.json()
