"""Agronomy knowledge retrieval grounding for damage assessments."""

from __future__ import annotations

from app.clients.vector_store import QueryHit, VectorDoc, get_store

COLLECTION = "agronomy_kb"


def upsert_docs(docs: list[VectorDoc]) -> None:
    get_store().upsert(COLLECTION, docs)


def retrieve(*, crop: str, damage_cause: str, k: int = 3) -> list[QueryHit]:
    """Pull the most relevant agronomy snippets for a given crop+damage scenario."""
    query = f"{crop} crop {damage_cause} damage symptoms recovery management"
    where: dict | None = None
    # Soft filter: prefer same-crop docs but don't require it (retrieval falls back to all)
    return get_store().query(COLLECTION, query, k=k, where=where)
