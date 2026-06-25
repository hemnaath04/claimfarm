"""Stripe billing API (checkout + webhook).

Sit-this-out gracefully when Stripe is not configured: checkout returns
a stub session; webhook accepts payloads and logs them. Real wiring
lights up when STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET are set.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.auth import tokens
from app.auth.routes import SESSION_COOKIE
from app.clients.stripe_client import PlanCode, create_checkout_session, parse_webhook
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
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = parse_webhook(payload=payload, signature=signature)
    except Exception as exc:  # noqa: BLE001
        logger.warning("invalid stripe webhook: %s", exc)
        raise HTTPException(status_code=400, detail="invalid signature") from exc

    audit(
        actor="stripe",
        action="billing.webhook",
        target=event.get("id"),
        metadata={"type": event.get("type")},
    )
    # TODO: handle checkout.session.completed, customer.subscription.updated,
    # invoice.payment_failed, etc. For now we just log.
    return {"received": True}
