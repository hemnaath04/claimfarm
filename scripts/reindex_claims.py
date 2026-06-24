"""Re-index every claim in SQLite into the vector store.

Useful after the vector store has been wiped, swapped, or when claims
existed before the RAG layer was wired in.

Usage:
    uv run python scripts/reindex_claims.py
"""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from app.agents.past_claim_rag import index_claim
from app.storage import claims_repo


def main() -> int:
    rows = claims_repo.list_by_status()
    print(f"Re-indexing {len(rows)} claim(s)...")
    for row in rows:
        claim = claims_repo.get(row.claim_id)
        if claim is None:
            continue
        index_claim(claim)
        print(f"  indexed {claim.claim_id}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
