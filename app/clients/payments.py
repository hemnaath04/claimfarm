"""Payments provider abstraction.

We don't ship Stripe in the default tree because creating a Stripe
account requires a US SSN + registered business that not every founder
has. Defaults to `none` (billing disabled — Pilot tier only). Real
deployments swap in any of:

- **Paddle** (paddle.com) — merchant-of-record, no business required,
  handles VAT/sales tax worldwide. Recommended for solo / international
  founders.
- **LemonSqueezy** (lemonsqueezy.com) — same MoR model as Paddle, very
  easy onboarding for individuals.
- **Razorpay** (razorpay.com) — India-based, ideal for INR / domestic.
- **PayPal** — universal, simple, higher fees.
- **Stripe** — once you have a US-EIN-registered LLC + SSN.

Each provider gets a thin wrapper that exposes `create_checkout_session`
and `verify_webhook`. While `PAYMENTS_PROVIDER=none`, both calls return
stubs so the rest of the system runs without touching a real payment
rail.
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


PLAN_PRICE_CENTS = {
    PlanCode.pilot: 0,
    PlanCode.growth: 85,        # cents per filed claim — usage-billed
    PlanCode.enterprise: 0,      # negotiated
}


@dataclass
class CheckoutSession:
    id: str
    url: str
    customer_id: str
    plan: PlanCode
    provider: str
    expires_at: datetime


def _provider_name() -> str:
    s = get_settings()
    return (getattr(s, "payments_provider", "none") or "none").lower()


def create_checkout_session(
    *,
    org_id: str,
    plan: PlanCode,
    success_url: str,
    cancel_url: str,
) -> CheckoutSession:
    """Open a hosted-checkout session at the configured provider, or a stub
    when billing is disabled.
    """
    name = _provider_name()
    if name == "none":
        logger.info("payments disabled — stub checkout for %s/%s", org_id, plan.value)
        return CheckoutSession(
            id=f"cs_stub_{secrets.token_urlsafe(12)}",
            url=success_url,
            customer_id=f"cus_stub_{org_id}",
            plan=plan,
            provider="none",
            expires_at=datetime.utcnow(),
        )

    if name == "paddle":
        return _paddle_checkout(org_id=org_id, plan=plan, success_url=success_url, cancel_url=cancel_url)
    if name == "lemonsqueezy":
        return _lemonsqueezy_checkout(org_id=org_id, plan=plan, success_url=success_url, cancel_url=cancel_url)
    if name == "razorpay":
        return _razorpay_checkout(org_id=org_id, plan=plan, success_url=success_url, cancel_url=cancel_url)

    raise RuntimeError(f"unknown payments provider: {name!r}")


def verify_webhook(*, payload: bytes, signature: str) -> dict:
    """Verify + parse a webhook from the configured provider."""
    import json

    name = _provider_name()
    if name == "none":
        logger.warning("payments disabled — accepting webhook without verification")
        return json.loads(payload or b"{}")
    if name == "paddle":
        return _paddle_verify_webhook(payload=payload, signature=signature)
    if name == "lemonsqueezy":
        return _lemonsqueezy_verify_webhook(payload=payload, signature=signature)
    if name == "razorpay":
        return _razorpay_verify_webhook(payload=payload, signature=signature)
    raise RuntimeError(f"unknown payments provider: {name!r}")


# ---------------------------------------------------------------------------
# Provider adapters (TODO bodies until the corresponding credentials land)
# ---------------------------------------------------------------------------


def _paddle_checkout(**_kwargs) -> CheckoutSession:
    # TODO: requires `PADDLE_API_KEY`. Use Paddle Billing's `/transactions`
    # endpoint to create a transaction with `collection_mode=automatic` and
    # return the hosted checkout URL.
    raise NotImplementedError("Paddle wiring needs PADDLE_API_KEY + product/price IDs")


def _paddle_verify_webhook(**_kwargs) -> dict:
    # TODO: HMAC-SHA256 the raw payload with the secret from
    # `PADDLE_WEBHOOK_SECRET`, compare to the `Paddle-Signature` header.
    raise NotImplementedError


def _lemonsqueezy_checkout(**_kwargs) -> CheckoutSession:
    # TODO: POST /v1/checkouts with the variant_id and return data.attributes.url
    raise NotImplementedError("LemonSqueezy wiring needs LEMONSQUEEZY_API_KEY + variant IDs")


def _lemonsqueezy_verify_webhook(**_kwargs) -> dict:
    # TODO: HMAC-SHA256 with LEMONSQUEEZY_WEBHOOK_SECRET vs X-Signature header.
    raise NotImplementedError


def _razorpay_checkout(**_kwargs) -> CheckoutSession:
    # TODO: requires `RAZORPAY_KEY_ID` + `RAZORPAY_KEY_SECRET`. Use the
    # Subscriptions API to create a subscription against a Plan and return
    # the short_url for the hosted checkout.
    raise NotImplementedError("Razorpay wiring needs RAZORPAY_KEY_ID + Plan IDs")


def _razorpay_verify_webhook(**_kwargs) -> dict:
    # TODO: verify x-razorpay-signature header with RAZORPAY_WEBHOOK_SECRET.
    raise NotImplementedError
