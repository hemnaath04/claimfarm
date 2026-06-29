"""Render a Claim into a PDF using WeasyPrint."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

# WeasyPrint depends on pango/cairo. On Apple Silicon, Homebrew installs them
# under /opt/homebrew/lib which isn't on the default dyld search path. Set it
# before importing weasyprint so the native libs resolve.
if sys.platform == "darwin":
    _brew_lib = "/opt/homebrew/lib"
    if Path(_brew_lib).is_dir():
        existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
        if _brew_lib not in existing.split(":"):
            os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
                f"{_brew_lib}:{existing}" if existing else _brew_lib
            )

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402
from weasyprint import HTML  # noqa: E402

from app.models.claim import Claim, Farmer  # noqa: E402
from app.models.damage import DamageAssessment  # noqa: E402
from app.models.weather import CorroborationResult, WeatherSummary  # noqa: E402


def upload_claim_pdf_to_oss(claim: Claim, pdf_path: str | Path) -> str:
    """Upload a rendered claim PDF to Alibaba OSS. Returns the OSS object URL."""
    from app.clients import alibaba_oss  # local import; OSS creds may be absent in dev

    key = f"claims/{claim.claim_id}.pdf"
    return alibaba_oss.upload_file(key, pdf_path)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


# Brand mark, inline so WeasyPrint renders it without a network fetch or file
# dependency (matches web/src/components/brand/logo.tsx).
LOGO_SVG = (
    '<svg width="38" height="38" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">'
    '<rect width="40" height="40" rx="10.5" fill="#F4C95D"/>'
    '<g transform="rotate(-38 20 20)">'
    '<path d="M20 5.5C28.5 11.5 28.5 28.5 20 34.5C11.5 28.5 11.5 11.5 20 5.5Z" '
    'transform="translate(2.3 2.1)" fill="#7FB3D2"/>'
    '<path d="M20 5.5C28.5 11.5 28.5 28.5 20 34.5C11.5 28.5 11.5 11.5 20 5.5Z" fill="#1F6E4E"/>'
    '</g>'
    '<path d="M14.8 20.6l3.6 3.6 7.2-8.4" transform="rotate(-6 20 20)" stroke="#FFFCF5" '
    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
    '</svg>'
)

_STATUS_LABELS = {
    "pending_review": "Under review",
    "approved": "Approved",
    "rejected": "Not approved",
    "submitted": "Submitted to insurer",
    "paid": "Paid",
}


def _verification(claim: Claim) -> dict:
    """Derive the red flags that block final approval and the proof each one
    needs. The document asks the farmer to email these proofs in for re-review.
    """
    from app.config import get_settings

    f = getattr(claim, "forensics", None)
    auth_pct = round(f.authenticity_score * 100) if f else None
    has_gps = bool(f and f.gps_lat is not None and f.gps_lon is not None)

    flags: list[dict] = []
    if auth_pct is not None and auth_pct < 85:
        flags.append({
            "title": f"Photo authenticity is {auth_pct}% (below the 85% needed to auto-approve)",
            "why": "The image may be a screenshot, a downloaded picture, or edited. "
                   "We can only pay claims backed by a genuine on-site photo.",
            "proof": "Send a fresh photo of the damaged crop taken right now on your "
                     "phone at the field. Do not crop, filter, or screenshot it.",
        })
    if not has_gps:
        flags.append({
            "title": "Field location not verified",
            "why": "The photo carries no GPS location, so we cannot confirm the damage "
                   "happened on your insured field.",
            "proof": "Prove the location: share your live location with the ClaimFarm "
                     "bot, or send a geotagged photo, or a wide photo of the field "
                     "showing a fixed landmark (a road, building, or tree line).",
        })
    if f is not None and not f.has_exif:
        flags.append({
            "title": "Camera details missing from the photo",
            "why": "The photo has no camera metadata, which usually means it was "
                   "downloaded or edited rather than taken on-site.",
            "proof": "Resend the original photo straight from your phone's camera roll, "
                     "unedited.",
        })
    if claim.corroboration is not None and not claim.corroboration.corroborated:
        flags.append({
            "title": "Weather records do not yet match the reported cause",
            "why": claim.corroboration.evidence
                   or "Weather data for your area and dates does not support the "
                      "reported damage cause.",
            "proof": "Provide extra dated evidence of the event: photos taken over "
                     "several days, or a note from your local agriculture office.",
        })

    status = claim.status.value
    needs = bool(flags)
    if status == "approved" and needs:
        decision = ("Approved in principle. Final payout is on hold until the "
                    "verification items below are confirmed.")
        tone = "amber"
    elif status == "approved":
        decision = (f"Approved. Estimated payout ${claim.estimated_loss_usd:,.2f} "
                    "will be processed to your registered account.")
        tone = "green"
    elif status == "rejected":
        decision = "Not approved." + (
            f" Reason: {claim.adjuster_notes}" if claim.adjuster_notes else ""
        )
        tone = "red"
    elif needs:
        decision = ("Received and under review. This claim cannot be finalized "
                    "until the verification items below are confirmed.")
        tone = "amber"
    else:
        decision = ("Received and under review by our adjuster. No further action "
                    "is needed from you right now.")
        tone = "amber"

    return {
        "logo_svg": LOGO_SVG,
        "status_label": _STATUS_LABELS.get(status, status),
        "decision": decision,
        "decision_tone": tone,
        "red_flags": flags,
        "needs_verification": needs,
        "authenticity_pct": auth_pct,
        "has_gps": has_gps,
        "support_email": get_settings().resend_reply_to or "help@hemnaath.tech",
    }


def render_claim_html(claim: Claim) -> str:
    template = _env.get_template("claim.html")
    return template.render(claim=claim, **_verification(claim))


def render_claim_pdf(claim: Claim, out_path: str | Path) -> Path:
    """Render the claim PDF and write it to `out_path`. Returns the path."""
    html = render_claim_html(claim)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(target=str(out))
    return out


def build_claim(
    *,
    farmer: Farmer,
    damage: DamageAssessment,
    weather: WeatherSummary,
    corroboration: CorroborationResult,
    date_of_damage: date,
    farmer_narrative: str = "",
    photo_urls: list[str] | None = None,
    forensics=None,  # PhotoForensics | None — kept loose to avoid an import cycle
    typical_yield_usd_per_hectare: float = 800.0,
) -> Claim:
    """Assemble a Claim object with a simple loss estimate.

    The loss model is intentionally crude for the hackathon scope:
        loss = farm_area * yield_per_ha * (severity/100) * (affected_area/100)
    """
    loss = (
        farmer.farm_area_hectares
        * typical_yield_usd_per_hectare
        * (damage.severity / 100.0)
        * (damage.affected_area_pct / 100.0)
    )
    return Claim(
        farmer=farmer,
        crop_type=damage.crop_type,
        date_of_damage=date_of_damage,
        photo_urls=photo_urls or [],
        farmer_narrative=farmer_narrative,
        damage=damage,
        weather=weather,
        corroboration=corroboration,
        forensics=forensics,
        estimated_loss_usd=round(loss, 2),
    )
