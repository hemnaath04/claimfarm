"""Vector store abstraction with Chroma (local) and DashVector (prod) backends.

Switch via the VECTOR_STORE env var (chroma | dashvector). The two backends
expose the same upsert/query API so call sites don't change.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.clients.embeddings import embed
from app.config import get_settings


@dataclass
class VectorDoc:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryHit:
    id: str
    score: float  # higher = more similar (cosine)
    text: str
    metadata: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, collection: str, docs: list[VectorDoc]) -> None: ...

    @abstractmethod
    def query(
        self,
        collection: str,
        text: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryHit]: ...

    @abstractmethod
    def delete(self, collection: str, ids: list[str]) -> None: ...

    @abstractmethod
    def count(self, collection: str) -> int: ...


def _serialize_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """Chroma metadata only accepts scalar values; serialize lists/dicts."""
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        else:
            out[k] = json.dumps(v)
    return out


def _deserialize_meta(meta: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if isinstance(v, str) and v.startswith(("{", "[")):
            try:
                out[k] = json.loads(v)
                continue
            except json.JSONDecodeError:
                pass
        out[k] = v
    return out


class ChromaStore(VectorStore):
    def __init__(self, persist_path: str | Path | None = None):
        import chromadb  # local import keeps cold-path costs out of unrelated modules

        s = get_settings()
        path = Path(persist_path or s.chroma_path)
        path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))

    def _coll(self, name: str):
        return self._client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, collection: str, docs: list[VectorDoc]) -> None:
        if not docs:
            return
        vectors = embed([d.text for d in docs])
        coll = self._coll(collection)
        coll.upsert(
            ids=[d.id for d in docs],
            embeddings=vectors,
            documents=[d.text for d in docs],
            metadatas=[_serialize_meta(d.metadata) for d in docs],
        )

    def query(
        self,
        collection: str,
        text: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryHit]:
        coll = self._coll(collection)
        q_vec = embed([text])[0]
        res = coll.query(
            query_embeddings=[q_vec],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = res["ids"][0] if res.get("ids") else []
        docs = res["documents"][0] if res.get("documents") else []
        metas = res["metadatas"][0] if res.get("metadatas") else []
        dists = res["distances"][0] if res.get("distances") else []
        out: list[QueryHit] = []
        for i, _id in enumerate(ids):
            # Chroma cosine distance ∈ [0,2]; convert to similarity ∈ [-1,1].
            sim = 1.0 - float(dists[i]) if i < len(dists) else 0.0
            out.append(
                QueryHit(
                    id=_id,
                    score=sim,
                    text=docs[i] if i < len(docs) else "",
                    metadata=_deserialize_meta(metas[i]) if i < len(metas) else {},
                )
            )
        return out

    def delete(self, collection: str, ids: list[str]) -> None:
        if not ids:
            return
        self._coll(collection).delete(ids=ids)

    def count(self, collection: str) -> int:
        return self._coll(collection).count()


class DashVectorStore(VectorStore):
    """Alibaba DashVector backend. Provisioned in Task #11 deployment work."""

    def __init__(self):
        from dashvector import Client  # type: ignore

        s = get_settings()
        if not s.dashvector_api_key or not s.dashvector_endpoint:
            raise RuntimeError(
                "DASHVECTOR_API_KEY and DASHVECTOR_ENDPOINT must be set "
                "(or use VECTOR_STORE=chroma for local dev)"
            )
        self._client = Client(api_key=s.dashvector_api_key, endpoint=s.dashvector_endpoint)

    def _coll(self, name: str):
        return self._client.get(name)  # assumes collection pre-created in console

    @staticmethod
    def _check(res, op: str) -> None:
        code = getattr(res, "code", None)
        if code not in (0, None):
            raise RuntimeError(
                f"DashVector {op} failed: code={code} message={getattr(res, 'message', '')}"
            )

    @staticmethod
    def _stringify_fields(meta: dict[str, Any]) -> dict[str, Any]:
        """DashVector fields accept scalars; serialize complex values."""
        out: dict[str, Any] = {}
        for k, v in meta.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[k] = v
            else:
                out[k] = json.dumps(v)
        return out

    def upsert(self, collection: str, docs: list[VectorDoc]) -> None:
        if not docs:
            return
        from dashvector import Doc  # type: ignore

        vectors = embed([d.text for d in docs])
        coll = self._coll(collection)
        items = [
            Doc(
                id=d.id,
                vector=v,
                fields=self._stringify_fields({**d.metadata, "text": d.text}),
            )
            for d, v in zip(docs, vectors)
        ]
        # DashVector caps batches at 100; chunk for safety.
        for i in range(0, len(items), 100):
            res = coll.upsert(items[i : i + 100])
            self._check(res, "upsert")

    def query(
        self,
        collection: str,
        text: str,
        *,
        k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[QueryHit]:
        coll = self._coll(collection)
        q_vec = embed([text])[0]
        filter_str = None
        if where:
            filter_str = " and ".join(f"{k_}='{v_}'" for k_, v_ in where.items())
        res = coll.query(
            vector=q_vec, topk=k, filter=filter_str, output_fields=None
        )
        self._check(res, "query")
        hits: list[QueryHit] = []
        for r in res.output or []:
            fields = dict(getattr(r, "fields", None) or {})
            text_val = fields.pop("text", "")
            hits.append(
                QueryHit(
                    id=str(r.id),
                    # DashVector returns cosine distance (lower = closer);
                    # convert to similarity for consistency with ChromaStore.
                    score=1.0 - float(r.score),
                    text=str(text_val),
                    metadata=_deserialize_meta(fields),
                )
            )
        return hits

    def delete(self, collection: str, ids: list[str]) -> None:
        if not ids:
            return
        res = self._coll(collection).delete(ids=ids)
        self._check(res, "delete")

    def count(self, collection: str) -> int:
        coll = self._coll(collection)
        stats = coll.stats() if hasattr(coll, "stats") else None
        return int(getattr(stats, "total_doc_count", 0) or 0)


_store: VectorStore | None = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        s = get_settings()
        backend = (s.vector_store or "chroma").lower()
        if backend == "dashvector":
            _store = DashVectorStore()
        else:
            _store = ChromaStore()
    return _store
