"""Seed the agronomy knowledge base with curated snippets.

Hackathon-scale: ~15 short paragraphs spanning common smallholder crops
and damage causes. In production this would be replaced by FAO / ICRISAT /
extension service guides indexed at scale.

Usage:
    uv run python scripts/seed_agronomy_kb.py
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from app.agents.agronomy_rag import upsert_docs
from app.clients.vector_store import VectorDoc

DOCS: list[tuple[str, str, dict]] = [
    (
        "rice-flood-01",
        "Rice (paddy) is partially flood-tolerant but submergence beyond seven days "
        "causes yield loss exceeding 50%. After flood recession, fields should be "
        "drained promptly and a top-dressing of nitrogen applied to surviving plants. "
        "Visible indicators of flood damage: standing water in fields, yellowing of "
        "lower leaves, lodged tillers, and silt deposits on leaf surfaces.",
        {"crop": "rice", "damage_cause": "flood", "language": "en"},
    ),
    (
        "rice-drought-01",
        "Rice is highly drought sensitive at panicle initiation and flowering. "
        "Symptoms include leaf rolling, tip browning, delayed flowering, and "
        "unfilled grains. Affected fields show patchy stunting and reduced tiller "
        "count. Recovery from severe drought after flowering is generally not "
        "possible; mitigation focuses on alternate wetting and drying irrigation.",
        {"crop": "rice", "damage_cause": "drought", "language": "en"},
    ),
    (
        "maize-drought-01",
        "Maize is most vulnerable to drought during the silking and grain-fill "
        "stages. Symptoms: leaf curling, grayish-green color, premature tasseling, "
        "and barren ears. Severe drought leaves fields with brown, dried leaves "
        "and stunted, ungerminated stands. Yield losses of 50-90% are typical "
        "when drought spans the flowering window.",
        {"crop": "maize", "damage_cause": "drought", "language": "en"},
    ),
    (
        "maize-pest-fall-armyworm",
        "Fall armyworm (Spodoptera frugiperda) larvae feed inside maize whorls, "
        "producing characteristic shot-hole patterns and frass (sawdust-like "
        "excrement) at the whorl base. Heavy infestations cause ragged leaves "
        "and stunted plants. Action threshold: 20% of plants showing fresh damage. "
        "Biological control via Trichogramma egg parasitoids is effective in "
        "smallholder systems.",
        {"crop": "maize", "damage_cause": "pest", "language": "en"},
    ),
    (
        "wheat-frost-01",
        "Wheat is most susceptible to frost during heading and flowering, when "
        "even brief exposure below -2°C can sterilize florets. Frost damage "
        "appears 3-7 days after the event as bleached spikelets, water-soaked "
        "stems, and prematurely whitened heads. Affected fields typically show "
        "patchy damage on low-lying ground where cold air pools overnight.",
        {"crop": "wheat", "damage_cause": "frost", "language": "en"},
    ),
    (
        "wheat-hail-01",
        "Hail damage on wheat shows as torn, shredded leaves, broken stems, and "
        "kernels knocked loose from heads. Yield impact depends on growth stage: "
        "pre-anthesis damage allows partial recovery, while post-anthesis hail "
        "is essentially unrecoverable. Look for bruising and water-soaked tissue "
        "on undamaged neighboring stems as confirmation that the event was hail "
        "and not wind.",
        {"crop": "wheat", "damage_cause": "hail", "language": "en"},
    ),
    (
        "cotton-pest-bollworm",
        "Pink bollworm (Pectinophora gossypiella) larvae bore into cotton bolls, "
        "leaving small exit holes, premature opening, and stained lint. Heavy "
        "infestations reduce both yield and fiber quality. Pheromone trap counts "
        "above eight moths per night signal economic threshold. Bt cotton "
        "varieties provide partial protection but resistance has been documented "
        "in South Asia.",
        {"crop": "cotton", "damage_cause": "pest", "language": "en"},
    ),
    (
        "soybean-disease-rust",
        "Soybean rust (Phakopsora pachyrhizi) appears as small tan to reddish-brown "
        "pustules on the underside of leaves, progressing to leaf yellowing, "
        "premature defoliation, and reduced pod fill. Cool, humid conditions favor "
        "spread. Yield loss can exceed 80% in unsprayed fields. Confirmation "
        "requires hand-lens inspection of pustules; field-level symptoms can "
        "resemble other foliar diseases.",
        {"crop": "soybean", "damage_cause": "disease", "language": "en"},
    ),
    (
        "general-flood-pattern",
        "Flood-damaged fields show consistent indicators across crops: standing "
        "or pooled water, silt deposits on leaves, prone or lodged plants, "
        "anaerobic root systems (blackened roots), and a sour smell from "
        "decomposing biomass. Damage extends along low-lying ground and "
        "drainage paths. Compare against rainfall records for the prior 30 "
        "days to corroborate.",
        {"crop": "any", "damage_cause": "flood", "language": "en"},
    ),
    (
        "general-drought-pattern",
        "Drought damage progresses from leaf rolling and color loss to wilting, "
        "premature senescence, and complete desiccation. Affected fields show "
        "uniform stunting (unlike pest damage which is patchy) and reduced or "
        "absent reproductive structures. Cross-check with consecutive dry-day "
        "counts and days above 35°C — drought verdict without low rainfall "
        "should be reviewed by an adjuster.",
        {"crop": "any", "damage_cause": "drought", "language": "en"},
    ),
    (
        "general-hail-pattern",
        "Hail damage is distinguishable from wind by directional, top-down "
        "shredding of leaves and bruising of stems. Smaller plants may be "
        "knocked sideways or buried in mud. Look for a contiguous damage "
        "swath rather than scattered damage. Hailstones leave pock-marks on "
        "neighboring soil and trash.",
        {"crop": "any", "damage_cause": "hail", "language": "en"},
    ),
    (
        "millet-drought-01",
        "Pearl millet and finger millet are far more drought tolerant than maize "
        "or rice but still suffer under prolonged dry spells. Symptoms include "
        "delayed panicle emergence, reduced grain filling, and forced senescence. "
        "Smallholders in arid regions often plant millet specifically as a "
        "drought-insurance crop; severe damage suggests an extreme event.",
        {"crop": "millet", "damage_cause": "drought", "language": "en"},
    ),
    (
        "sorghum-pest-shoot-fly",
        "Sorghum shoot fly (Atherigona soccata) attacks seedlings in the first "
        "30 days, producing characteristic 'dead heart' symptoms — central whorl "
        "dries up while older leaves remain green. Heavy infestation in early "
        "monsoon plantings can reduce stands by 80%. Seed treatment and early "
        "sowing are the main control tactics.",
        {"crop": "sorghum", "damage_cause": "pest", "language": "en"},
    ),
    (
        "groundnut-disease-rosette",
        "Groundnut rosette virus, transmitted by Aphis craccivora, produces "
        "stunted plants with small, distorted, chlorotic leaves giving a "
        "rosette appearance. Affected plants rarely set pods. Disease pressure "
        "is highest in late-planted crops; resistant varieties and aphid "
        "control are the main management tools in West and East Africa.",
        {"crop": "groundnut", "damage_cause": "disease", "language": "en"},
    ),
    (
        "general-wind-pattern",
        "Wind damage shows directional lodging — plants laid down in a "
        "consistent compass direction. Stem breakage at the base distinguishes "
        "severe wind events from waterlogging-induced lodging. Wind alone "
        "rarely causes leaf shredding; if shredded leaves accompany lodging, "
        "suspect a combined hail + wind event.",
        {"crop": "any", "damage_cause": "wind", "language": "en"},
    ),
]


def main() -> int:
    docs = [VectorDoc(id=id_, text=text, metadata=meta) for id_, text, meta in DOCS]
    upsert_docs(docs)
    print(f"Indexed {len(docs)} agronomy snippets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
