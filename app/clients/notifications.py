"""Multi-channel notification abstraction (email, sms, push, in-app).

The application code calls `send(kind, recipient, template, vars)` and the
notification layer routes to the right transport based on the recipient's
preferences. Transports are pluggable — Resend for email, Twilio for SMS,
APNs/FCM for push — and fall through to logging when not configured.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from app.clients import email_layout
from app.config import get_settings

logger = logging.getLogger(__name__)


_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "claimfarm-mark.png"
_logo_b64_cache: str | None = None


def _logo_attachment() -> dict[str, Any] | None:
    """The brand mark as an inline (cid) Resend attachment, base64-cached."""
    global _logo_b64_cache
    try:
        if _logo_b64_cache is None:
            _logo_b64_cache = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
        return {
            "filename": "claimfarm-mark.png",
            "content": _logo_b64_cache,
            "content_type": "image/png",
            "content_id": "claimfarm-logo",
        }
    except Exception:
        logger.exception("could not load inline logo at %s", _LOGO_PATH)
        return None


def email_transport_configured() -> bool:
    """True when a real outbound provider is wired up. Auth endpoints
    use this to decide whether to return verification URLs inline."""
    s = get_settings()
    return bool(s.resend_api_key or s.sendgrid_api_key)


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


def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
) -> NotificationResult:
    """Send an email. `body` is the plain-text part; `html` (optional) is the
    rendered HTML — when omitted we wrap the plain body in the branded layout
    so every email is consistently styled. `attachments` is a list of Resend
    attachment dicts: ``{"filename": str, "content": <base64 str>}``.
    """
    s = get_settings()
    if html is None:
        blocks, button = email_layout.auto_blocks_from_text(body)
        html = email_layout.render_email(heading=subject, blocks=blocks, button=button)
    if s.resend_api_key:
        return _send_email_resend(
            to=to, subject=subject, text=body, html=html, attachments=attachments
        )
    # Fall through to log-only so dev flows keep working without keys.
    logger.info("EMAIL→%s · %s · %s", to, subject, body[:120])
    return NotificationResult(channel=Channel.email, delivered=True, provider="log")


def _send_email_resend(
    *,
    to: str,
    subject: str,
    text: str,
    html: str,
    attachments: list[dict[str, Any]] | None = None,
) -> NotificationResult:
    """Send via Resend's REST API.

    Resend's free tier is 100/day, 3 000/month, no business / SSN gate,
    and the API is a single POST so we don't need their Python SDK. The
    sender address must come from a verified domain — until the user
    adds their own, ``onboarding@resend.dev`` works for any inbox.
    """
    s = get_settings()
    payload: dict[str, Any] = {
        "from": s.resend_from,
        "to": [to],
        "subject": subject,
        "html": html,
        "text": text,
    }
    if s.resend_reply_to:
        payload["reply_to"] = s.resend_reply_to
    # Embed the brand logo inline (cid:claimfarm-logo) so the header mark shows
    # without the client's "display images" prompt, then any caller attachments.
    all_attachments: list[dict[str, Any]] = []
    logo = _logo_attachment()
    if logo:
        all_attachments.append(logo)
    if attachments:
        all_attachments.extend(attachments)
    if all_attachments:
        payload["attachments"] = all_attachments
    try:
        r = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {s.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
        if r.status_code >= 400:
            logger.warning("resend: %s · %s", r.status_code, r.text[:300])
            return NotificationResult(
                channel=Channel.email,
                delivered=False,
                provider="resend",
                detail=f"{r.status_code} {r.text[:200]}",
            )
        return NotificationResult(channel=Channel.email, delivered=True, provider="resend")
    except httpx.HTTPError as exc:
        logger.exception("resend transport failed")
        return NotificationResult(
            channel=Channel.email,
            delivered=False,
            provider="resend",
            detail=str(exc),
        )


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
            "ClaimFarm"
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


# ---------------------------------------------------------------------------
# Branded transactional emails (explicit layout + CTA button)
# ---------------------------------------------------------------------------


def send_verify_email(*, to: str, name: str, url: str) -> NotificationResult:
    """Email-address verification ("OTP") link after sign-up / accept-invite."""
    hi = f"Welcome to ClaimFarm, {name}." if name else "Welcome to ClaimFarm."
    blocks = [
        hi,
        "Confirm this email address to activate your account and start "
        "reviewing claims. This link expires in 24 hours.",
    ]
    html = email_layout.render_email(
        heading="Verify your email",
        blocks=blocks,
        button=("Verify my email", url),
        footnote="If you didn't create a ClaimFarm account, you can ignore this email.",
    )
    text = email_layout.render_plaintext("Verify your email", blocks, ("Verify my email", url))
    return send_email(to=to, subject="Verify your ClaimFarm email", body=text, html=html)


def send_reset_email(*, to: str, url: str) -> NotificationResult:
    blocks = [
        "We received a request to reset your ClaimFarm password.",
        "Click the button below to choose a new one. This link expires in 1 hour.",
    ]
    html = email_layout.render_email(
        heading="Reset your password",
        blocks=blocks,
        button=("Reset password", url),
        footnote="Didn't ask for this? Your password is unchanged, so you can ignore this email.",
    )
    text = email_layout.render_plaintext("Reset your password", blocks, ("Reset password", url))
    return send_email(to=to, subject="Reset your ClaimFarm password", body=text, html=html)


def send_magic_link_email(*, to: str, url: str) -> NotificationResult:
    blocks = [
        "Here's your one-tap sign-in link for ClaimFarm.",
        "It signs you straight into the console and expires in 15 minutes.",
    ]
    html = email_layout.render_email(
        heading="Your sign-in link",
        blocks=blocks,
        button=("Sign in to ClaimFarm", url),
        footnote="If you didn't request this link, you can safely ignore it.",
    )
    text = email_layout.render_plaintext("Your sign-in link", blocks, ("Sign in", url))
    return send_email(to=to, subject="Your ClaimFarm sign-in link", body=text, html=html)


def send_invite_email(*, to: str, inviter: str, role: str, url: str) -> NotificationResult:
    """Invite-only access: the owner issues these from the admin console."""
    who = f"{inviter} has invited you" if inviter else "You've been invited"
    blocks = [
        f"{who} to join ClaimFarm as a {role}.",
        "Accept the invitation to set your password and get access to the "
        "adjuster console. This invite expires in 7 days.",
    ]
    html = email_layout.render_email(
        heading="You're invited to ClaimFarm",
        blocks=blocks,
        button=("Accept invitation", url),
        footnote="If you weren't expecting this, you can ignore the email; the invite stays unused.",
    )
    text = email_layout.render_plaintext("You're invited to ClaimFarm", blocks, ("Accept invitation", url))
    return send_email(to=to, subject="You're invited to ClaimFarm", body=text, html=html)


def send_claim_pdf_email(
    *, to: str, claim_id: str, farmer_name: str, pdf_bytes: bytes
) -> NotificationResult:
    """Email the farmer their claim summary PDF as an attachment, on request."""
    import base64

    blocks = [
        f"Hi {farmer_name}," if farmer_name else "Hi,",
        f"Attached is the PDF summary for your crop-insurance claim {claim_id}.",
        "Keep it for your records. It lists the assessed damage, the weather "
        "check, and the current claim status.",
    ]
    html = email_layout.render_email(
        heading=f"Your claim {claim_id}",
        blocks=blocks,
        footnote="Questions? Reply to the ClaimFarm bot on Telegram.",
    )
    text = email_layout.render_plaintext(f"Your claim {claim_id}", blocks, None)
    attachments = [
        {
            "filename": f"{claim_id}.pdf",
            "content": base64.b64encode(pdf_bytes).decode("ascii"),
        }
    ]
    return send_email(
        to=to,
        subject=f"Your ClaimFarm claim {claim_id}",
        body=text,
        html=html,
        attachments=attachments,
    )


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
