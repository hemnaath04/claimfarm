"""Smoke test for the vector store + RAG layer.

Run AFTER seeding agronomy:
    uv run python scripts/seed_agronomy_kb.py
    uv run python scripts/test_rag.py
"""

from __future__ import annotations

from datetime import date

from dotenv import load_dotenv

load_dotenv()

from app.agents import agronomy_rag, fraud_check, past_claim_rag
from app.clients.vector_store import get_store
from app.models.claim import Claim, ClaimStatus, Farmer
from app.models.damage import DamageAssessment, DamageCause
from app.models.weather import CorroborationResult, WeatherSummary


def _claim(claim_id: str, *, phone: str, narrative: str, severity: int, cause: DamageCause) -> Claim:
    return Claim(
        claim_id=claim_id,
        farmer=Farmer(
            name="Demo Farmer",
            phone=phone,
            language="en",
            latitude=20.5,
            longitude=78.9,
            region="Demo",
            farm_area_hectares=2.0,
        ),
        crop_type="maize",
        date_of_damage=date(2026, 6, 1),
        damage=DamageAssessment(
            crop_type="maize",
            damage_cause=cause,
            severity=severity,
            affected_area_pct=80,
            confidence=0.9,
            visible_indicators=["dry leaves", "stunted growth"],
            notes="Field looks dried out, ears underdeveloped.",
        ),
        weather=WeatherSummary(
            latitude=20.5,
            longitude=78.9,
            start_date=date(2026, 5, 2),
            end_date=date(2026, 6, 1),
            total_precip_mm=12.0,
            max_temp_c=39.0,
            min_temp_c=22.0,
            max_wind_kmh=18.0,
            days_above_35c=18,
            days_with_heavy_rain=0,
            days_with_frost=0,
            consecutive_dry_days=20,
        ),
        corroboration=CorroborationResult(
            corroborated=True, strength=0.88, evidence="Low rainfall + many hot days."
        ),
        estimated_loss_usd=1200.0,
        status=ClaimStatus.pending_review,
        farmer_narrative=narrative,
    )


def main() -> int:
    print("Vector backend:", type(get_store()).__name__)

    print("\n=== Agronomy retrieval ===")
    hits = agronomy_rag.retrieve(crop="maize", damage_cause="drought", k=3)
    for h in hits:
        print(f"  {h.score:.3f}  {h.id}  ({h.metadata.get('crop')}/{h.metadata.get('damage_cause')})")
        print(f"         {h.text[:120]}...")

    print("\n=== Index three past claims (two from same farmer, one different) ===")
    a = _claim("CF-TEST-A", phone="+91-555-0001", narrative="Maize field dried up after no rain.", severity=85, cause=DamageCause.drought)
    b = _claim("CF-TEST-B", phone="+91-555-0001", narrative="Cornfield completely dried out, no rain for weeks.", severity=88, cause=DamageCause.drought)
    c = _claim("CF-TEST-C", phone="+91-555-0002", narrative="Flooded paddy field after monsoon storm.", severity=70, cause=DamageCause.flood)
    for x in (a, b, c):
        past_claim_rag.index_claim(x)
    print("  Indexed three.")

    print("\n=== Find similar past claims to a new drought claim ===")
    new = _claim("CF-TEST-NEW", phone="+91-555-0003", narrative="Drought hit my corn, no harvest possible.", severity=80, cause=DamageCause.drought)
    similar = past_claim_rag.find_similar(new, k=3)
    for h in similar:
        print(f"  {h.score:.3f}  {h.metadata.get('claim_id')} (farmer {h.metadata.get('farmer_phone')})")

    print("\n=== Fraud check: same farmer resubmits near-identical claim ===")
    dupe = _claim("CF-TEST-DUPE", phone="+91-555-0001", narrative="Maize field dried up after no rain.", severity=85, cause=DamageCause.drought)
    flags = fraud_check.check(dupe)
    if flags:
        for f in flags:
            print(f"  [{f.severity}] {f.message}")
    else:
        print("  No flags raised.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
