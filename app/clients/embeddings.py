"""Qwen text-embedding-v3 wrapper.

Returned vectors are 1024-dim by default.
"""

from __future__ import annotations

from app.clients.qwen import get_client
from app.config import get_settings


BATCH_LIMIT = 10  # DashScope hard cap


def embed(texts: list[str], *, model: str | None = None) -> list[list[float]]:
    """Embed a list of strings. DashScope caps batches at 10 inputs, so we
    chunk transparently. Returns vectors in input order (1024-dim default).
    """
    if not texts:
        return []
    s = get_settings()
    client = get_client()
    mdl = model or s.qwen_embed_model

    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_LIMIT):
        chunk = texts[i : i + BATCH_LIMIT]
        resp = client.embeddings.create(model=mdl, input=chunk)
        out.extend(item.embedding for item in resp.data)
    return out


def embed_one(text: str, *, model: str | None = None) -> list[float]:
    return embed([text], model=model)[0]
