"""Append-only audit log of every state-changing event."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

# In production this would land in Tablestore or a dedicated audit DB with
# write-only credentials. For hackathon scope, a JSON-Lines file is enough
# and trivial to ship / inspect.
LOG_PATH = Path("/tmp/claimfarm_audit.jsonl")
_LOCK = Lock()


def record(
    *,
    actor: str,
    action: str,
    target: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append one row to the audit log.

    `actor` should be a user id, "system", or "api_key:<short_id>". Don't
    put PII in the metadata blob — only IDs, counts, and decision codes.
    """
    row = {
        "at": datetime.utcnow().isoformat() + "Z",
        "actor": actor,
        "action": action,
        "target": target,
        "metadata": metadata or {},
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK, LOG_PATH.open("a") as fh:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    except Exception:
        logger.exception("audit log write failed for %s", action)


def tail(n: int = 50) -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    try:
        lines = LOG_PATH.read_text().splitlines()[-n:]
        return [json.loads(line) for line in lines if line.strip()]
    except Exception:
        logger.exception("audit log read failed")
        return []
