"""Multi-channel notification abstraction (email, sms, push, in-app).

The application code calls `send(kind, recipient, template, vars)` and the
notification layer routes to the right transport based on the recipient's
preferences. Transports are pluggable — Resend for email, Twilio for SMS,
APNs/FCM for push — and fall through to logging when not configured.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Channel(str, Enum):
    email = "email"
    sms = "sms"
    push = "push"
    in_app = "in_app"


@dataclass
class NotificationResult:
    channel: Channel
    delivered: bool
    provider: str
    detail: str = ""


# In-memory in-app inbox so the dashboard can render unread items without
# a real DB. Production swaps this for a Tablestore-backed queue.
_INBOX: list[dict[str, Any]] = []


def render_template(template: str, vars: dict[str, Any]) -> str:
    """Tiny templating — replace {var} tokens. Real deploys would use
    Jinja or a managed template store (Resend, SendGrid)."""
    out = template
    for k, v in vars.items():
        out = out.replace("{" + k + "}", str(v))
    return out


def send_email(*, to: str, subject: str, body: str) -> NotificationResult:
    # TODO: integrate Resend / SendGrid / SES when credentials are set.
    logger.info("EMAIL→%s · %s · %s", to, subject, body[:120])
    return NotificationResult(channel=Channel.email, delivered=True, provider="log")


def send_sms(*, to: str, body: str) -> NotificationResult:
    # TODO: integrate Twilio Programmable SMS or Vonage.
    logger.info("SMS→%s · %s", to, body[:160])
    return NotificationResult(channel=Channel.sms, delivered=True, provider="log")


def push_in_app(*, user_id: str, title: str, body: str, link: str | None = None) -> NotificationResult:
    _INBOX.append({"user_id": user_id, "title": title, "body": body, "link": link, "unread": True})
    return NotificationResult(channel=Channel.in_app, delivered=True, provider="memory")


def inbox(user_id: str) -> list[dict[str, Any]]:
    return [n for n in _INBOX if n["user_id"] == user_id]


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "welcome": {
        "subject": "Welcome to ClaimFarm",
        "body": (
            "Hi {name},\n\n"
            "Thanks for creating a ClaimFarm pilot account. Your first 100 "
            "claims are on us. Verify your email to start filing:\n\n"
            "{verification_url}\n\n"
            "— ClaimFarm"
        ),
    },
    "claim_filed": {
        "subject": "Claim {claim_id} filed",
        "body": (
            "A new claim has been filed: {claim_id}\n"
            "Farmer: {farmer_name}\n"
            "Crop: {crop_type}\n"
            "Estimated loss: ${estimated_loss_usd}\n\n"
            "Review: {dashboard_url}/admin"
        ),
    },
    "fraud_flag": {
        "subject": "Risk flag on claim {claim_id}",
        "body": (
            "Claim {claim_id} raised a {severity} fraud signal:\n\n"
            "{message}\n\n"
            "Review: {dashboard_url}/admin"
        ),
    },
    "identity_approved": {
        "subject": "Identity verified",
        "body": (
            "Hi {name}, your identity was verified successfully. "
            "You can now file claims on behalf of your farmers."
        ),
    },
    "identity_review": {
        "subject": "Identity verification needs review",
        "body": (
            "Hi {name}, your identity-verification session needs additional "
            "review. A ClaimFarm specialist will reach out within 24 hours."
        ),
    },
}


def send(
    *,
    kind: str,
    user_id: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    channels: tuple[Channel, ...] = (Channel.in_app, Channel.email),
    vars: dict[str, Any] | None = None,
) -> list[NotificationResult]:
    """High-level dispatcher. Picks templates by `kind` and fans out."""
    tpl = TEMPLATES.get(kind)
    if tpl is None:
        raise KeyError(f"unknown notification kind: {kind}")
    rendered_subject = render_template(tpl["subject"], vars or {})
    rendered_body = render_template(tpl["body"], vars or {})
    results: list[NotificationResult] = []
    for ch in channels:
        if ch is Channel.email and email:
            results.append(send_email(to=email, subject=rendered_subject, body=rendered_body))
        elif ch is Channel.sms and phone:
            results.append(send_sms(to=phone, body=rendered_body))
        elif ch is Channel.in_app and user_id:
            results.append(push_in_app(user_id=user_id, title=rendered_subject, body=rendered_body))
    return results
