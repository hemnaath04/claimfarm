"""Client for the (mock) InsurerCo REST API.

By default this calls the bundled mock insurer **in-process** (no network),
which is robust on Function Compute where the server's internal port is not
8000. Set INSURER_BASE_URL to point at a real downstream carrier over HTTP.
"""

from __future__ import annotations

import os

import httpx

from app.models.claim import Claim

# Empty by default → call the mounted mock insurer in-process. Set to a real
# carrier base URL (e.g. https://api.insurer.example/v1) to submit over HTTP.
INSURER_BASE_URL = os.environ.get("INSURER_BASE_URL", "").rstrip("/")


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
    payload = _submission_payload(claim, pdf_url)
    target = (base_url or INSURER_BASE_URL).rstrip("/")
    if target:
        r = httpx.post(target + "/claims", json=payload, timeout=15.0)
        r.raise_for_status()
        return r.json()
    # In-process: call the mock insurer directly — no HTTP, no port binding.
    from mock_insurer.main import ClaimSubmission, submit_claim

    record = submit_claim(ClaimSubmission(**payload))
    return record.model_dump(mode="json")


def get(insurer_claim_id: str, *, base_url: str | None = None) -> dict:
    target = (base_url or INSURER_BASE_URL).rstrip("/")
    if target:
        r = httpx.get(target + f"/claims/{insurer_claim_id}", timeout=15.0)
        r.raise_for_status()
        return r.json()
    from mock_insurer.main import get_claim

    record = get_claim(insurer_claim_id)
    return record.model_dump(mode="json")
