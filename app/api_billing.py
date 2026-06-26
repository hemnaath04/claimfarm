"""Billing API (provider-agnostic checkout + webhook).

The underlying provider is selectable via PAYMENTS_PROVIDER:
- `none` (default) — checkout returns a stub, webhook just logs
- `paddle` | `lemonsqueezy` | `razorpay` — wire when credentials land

Stripe was intentionally removed because account creation requires a US
SSN + registered business. Paddle and LemonSqueezy are merchant-of-record
alternatives that work for solo / international founders.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.clients.payments import PlanCode, create_checkout_session, verify_webhook
from app.config import get_settings
from app.storage import users_repo
from app.storage.audit_log import record as audit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _require_user(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE, "")
    user_id = tokens.get_session_user(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user_id


@router.post("/checkout")
def checkout(request: Request, plan: str = "growth") -> dict:
    user_id = _require_user(request)
    row = users_repo.get(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    try:
        plan_code = PlanCode(plan)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    base = get_settings().public_base_url.rstrip("/")
    session = create_checkout_session(
        org_id=row.org_id or "default",
        plan=plan_code,
        success_url=f"{base}/dashboard?billing=success",
        cancel_url=f"{base}/pricing?billing=cancel",
    )
    audit(actor=user_id, action="billing.checkout_started", target=session.id, metadata={"plan": plan_code.value})
    return {
        "session_id": session.id,
        "url": session.url,
        "customer_id": session.customer_id,
        "plan": session.plan.value,
    }


@router.post("/webhook")
async def webhook(request: Request) -> dict:
    """Provider-neutral webhook entry point. The configured provider's
    signature header (Paddle-Signature / X-Signature / x-razorpay-signature)
    is forwarded into verify_webhook; the chosen adapter does the
    actual HMAC check."""
    payload = await request.body()
    signature = (
        request.headers.get("paddle-signature")
        or request.headers.get("x-signature")
        or request.headers.get("x-razorpay-signature")
        or ""
    )
    try:
        event = verify_webhook(payload=payload, signature=signature)
    except Exception as exc:  # noqa: BLE001
        logger.warning("invalid payments webhook: %s", exc)
        raise HTTPException(status_code=400, detail="invalid signature") from exc

    audit(
        actor="payments_provider",
        action="billing.webhook",
        target=event.get("id") or event.get("event_id"),
        metadata={"type": event.get("event_type") or event.get("type")},
    )
    # TODO: route handler dispatch by event type (subscription.created,
    # subscription.cancelled, payment.failed, …) once a provider is wired.
    return {"received": True}
