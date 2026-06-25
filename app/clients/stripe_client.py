"""Stripe payments abstraction.

Production deployments install the `stripe` Python package and provide
STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET. When unset, the module returns
deterministic stub responses so the rest of the system can be wired and
demoed end-to-end without burning real charges.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.config import get_settings

logger = logging.getLogger(__name__)


class PlanCode(str, Enum):
    pilot = "pilot"
    growth = "growth"
    enterprise = "enterprise"


PLAN_PRICES = {
    PlanCode.pilot: 0,
    PlanCode.growth: 85,          # cents per filed claim — usage-billed
    PlanCode.enterprise: 0,        # negotiated
}


@dataclass
class CheckoutSession:
    id: str
    url: str
    customer_id: str
    plan: PlanCode
    expires_at: datetime


def _stripe_configured() -> bool:
    s = get_settings()
    return bool(getattr(s, "stripe_secret_key", ""))


def create_checkout_session(
    *,
    org_id: str,
    plan: PlanCode,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    """Create a Stripe Checkout session for the upgrade flow.

    When STRIPE_SECRET_KEY is not configured we return a stub session that
    the dashboard can still show — clicking the URL simply lands on the
    cancel/success page locally.
    """
    if not _stripe_configured():
        logger.info("Stripe not configured — returning stub checkout for %s/%s", org_id, plan.value)
        return CheckoutSession(
            id=f"cs_stub_{secrets.token_urlsafe(12)}",
            url=success_url,
            customer_id=f"cus_stub_{org_id}",
            plan=plan,
            expires_at=datetime.utcnow(),
        )

    # TODO: import stripe; stripe.api_key = s.stripe_secret_key
    # TODO: session = stripe.checkout.Session.create(... metadata={"org_id": org_id} ...)
    # TODO: return CheckoutSession.from_stripe(session)
    raise NotImplementedError(
        "Stripe path requires the `stripe` package and a real STRIPE_SECRET_KEY. "
        "See deploy/README.md."
    )


def parse_webhook(*, payload: bytes, signature: str) -> dict:
    """Verify + parse a Stripe webhook. Returns the event dict.

    When STRIPE_WEBHOOK_SECRET is unset, we skip signature verification and
    json.loads the payload as-is — only safe for local dev.
    """
    s = get_settings()
    webhook_secret = getattr(s, "stripe_webhook_secret", "")
    if not webhook_secret:
        import json

        logger.warning("STRIPE_WEBHOOK_SECRET unset — skipping signature verification")
        return json.loads(payload)

    # TODO: import stripe; event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    # TODO: return event
    raise NotImplementedError("verified Stripe webhook path requires the stripe package")
