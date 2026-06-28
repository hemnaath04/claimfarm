"""JSON API exposing farmer profiles to the adjuster dashboard.

Read-only and admin-gated (same auth as the claims API): a farmer profile
carries PII (name, phone, email, location), so none of these routes may be
reachable anonymously.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api_claims import require_auth
from app.storage import claims_repo, farmer_repo

# Every route on this router requires authentication.
router = APIRouter(prefix="/api", tags=["farmers"], dependencies=[Depends(require_auth)])


def _claim_count_for(phone: str) -> int:
    """Number of claims filed by the farmer with this `phone`.

    A claim's `farmer_phone` mirrors the profile's `phone` (both are
    f"telegram:{chat_id}" for Telegram-sourced claims). An empty phone — a
    profile mid-registration — matches no claims.
    """
    if not phone:
        return 0
    rows = claims_repo.list_by_status()
    return sum(1 for r in rows if r.farmer_phone == phone)


@router.get("/farmers")
def list_farmers() -> dict[str, Any]:
    profiles = farmer_repo.list_all()
    items = [
        {
            "farmer_id": p.farmer_id,
            "name": p.name,
            "language": p.language,
            "region": p.region,
            "village": p.village,
            "crops": p.crops,
            "farm_area_hectares": p.farm_area_hectares,
            "email": p.email,
            "phone": p.phone,
            "channel": p.channel,
            "registration_complete": p.registration_complete,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "claim_count": _claim_count_for(p.phone),
        }
        for p in profiles
    ]
    return {"items": items, "total": len(items)}
