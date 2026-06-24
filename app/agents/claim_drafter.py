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


def render_claim_html(claim: Claim) -> str:
    template = _env.get_template("claim.html")
    return template.render(claim=claim)


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
        estimated_loss_usd=round(loss, 2),
    )
