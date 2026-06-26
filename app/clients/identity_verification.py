"""Identity-verification provider abstraction (KYC + liveness).

Production deployments swap in Persona, Veriff, or Onfido by setting
`IDENTITY_PROVIDER` and the matching credentials. With no provider
configured we fall back to `MockProvider`, which returns
deterministic-but-realistic results so the rest of the system can be
tested end-to-end without third-party costs.

Stripe Identity is intentionally not in this list — it requires a
Stripe account which needs a US SSN + registered business. The three
listed providers accept individual / international developers.
"""

from __future__ import annotations

import hashlib
import logging
import random
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol

from app.config import get_settings

logger = logging.getLogger(__name__)


class IdvDecision(str, Enum):
    approved = "approved"
    needs_review = "needs_review"
    rejected = "rejected"


@dataclass
class IdvResult:
    session_id: str
    decision: IdvDecision
    score: float                              # 0.0 = fail, 1.0 = pass
    extracted_name: str | None = None
    extracted_dob: str | None = None
    extracted_document_id: str | None = None
    document_country: str | None = None
    selfie_match_score: float | None = None
    liveness_score: float | None = None
    flags: list[str] = field(default_factory=list)
    provider: str = "mock"
    started_at: datetime = field(default_factory=datetime.utcnow)


class IdentityProvider(Protocol):
    name: str

    def start_session(self, *, user_id: str, return_url: str) -> dict:
        ...

    def evaluate(self, *, session_id: str) -> IdvResult:
        ...


# ---------------------------------------------------------------------------
# Mock provider (default until real credentials are configured)
# ---------------------------------------------------------------------------


class MockProvider:
    """Deterministic mock for demos. Each session_id yields a stable result
    based on a hash, so QA can target specific scenarios by user_id."""

    name = "mock"

    def start_session(self, *, user_id: str, return_url: str) -> dict:
        session_id = f"idv_mock_{secrets.token_urlsafe(16)}"
        logger.info("MockProvider session %s for %s", session_id, user_id)
        return {
            "session_id": session_id,
            # In real life this is the provider's hosted verification URL the
            # user is redirected to. We return the local dashboard URL here.
            "hosted_url": f"{return_url}?session={session_id}",
            "provider": self.name,
        }

    def evaluate(self, *, session_id: str) -> IdvResult:
        # Stable scoring based on session_id so the same id always returns
        # the same result. Useful for repeatable demos and integration tests.
        seed = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        score = round(rng.uniform(0.55, 0.99), 3)
        liveness = round(rng.uniform(0.6, 0.98), 3)
        selfie_match = round(rng.uniform(0.65, 0.99), 3)

        decision = IdvDecision.approved
        flags: list[str] = []
        if score < 0.7:
            decision = IdvDecision.needs_review
            flags.append("low_overall_score")
        if liveness < 0.7:
            decision = IdvDecision.needs_review
            flags.append("low_liveness")
        if selfie_match < 0.7:
            decision = IdvDecision.rejected
            flags.append("selfie_mismatch")

        return IdvResult(
            session_id=session_id,
            decision=decision,
            score=score,
            extracted_name=f"Mock User {seed % 1000:03d}",
            extracted_dob="1990-01-01",
            extracted_document_id=f"MOCK-{seed:08x}".upper(),
            document_country="IN",
            selfie_match_score=selfie_match,
            liveness_score=liveness,
            flags=flags,
            provider=self.name,
        )


# ---------------------------------------------------------------------------
# Real providers (Persona / Veriff / Onfido)
# ---------------------------------------------------------------------------
#
# Each real provider needs a small subclass implementing start_session +
# evaluate against its own SDK. We ship the shape here and leave the bodies
# as TODO until credentials are provisioned. Set IDENTITY_PROVIDER=<name>.


class PersonaProvider:
    name = "persona"

    def __init__(self) -> None:
        s = get_settings()
        if not getattr(s, "persona_api_key", ""):
            raise RuntimeError("PERSONA_API_KEY must be set for persona")
        # TODO: store + call POST /api/v1/inquiries with the inquiry-template-id
        raise NotImplementedError("Persona not yet wired — set PERSONA_API_KEY")

    def start_session(self, *, user_id: str, return_url: str) -> dict:  # noqa: ARG002
        raise NotImplementedError

    def evaluate(self, *, session_id: str) -> IdvResult:  # noqa: ARG002
        raise NotImplementedError


class VeriffProvider:
    name = "veriff"

    def __init__(self) -> None:
        s = get_settings()
        if not getattr(s, "veriff_api_key", ""):
            raise RuntimeError("VERIFF_API_KEY must be set for veriff")
        raise NotImplementedError("Veriff not yet wired — set VERIFF_API_KEY")

    def start_session(self, *, user_id: str, return_url: str) -> dict:  # noqa: ARG002
        raise NotImplementedError

    def evaluate(self, *, session_id: str) -> IdvResult:  # noqa: ARG002
        raise NotImplementedError


class OnfidoProvider:
    name = "onfido"

    def __init__(self) -> None:
        s = get_settings()
        if not getattr(s, "onfido_api_key", ""):
            raise RuntimeError("ONFIDO_API_KEY must be set for onfido")
        raise NotImplementedError("Onfido not yet wired — set ONFIDO_API_KEY")

    def start_session(self, *, user_id: str, return_url: str) -> dict:  # noqa: ARG002
        raise NotImplementedError

    def evaluate(self, *, session_id: str) -> IdvResult:  # noqa: ARG002
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDERS = {
    "persona": PersonaProvider,
    "veriff": VeriffProvider,
    "onfido": OnfidoProvider,
}


def get_provider() -> IdentityProvider:
    s = get_settings()
    name = (getattr(s, "identity_provider", "mock") or "mock").lower()
    cls = _PROVIDERS.get(name)
    if cls is None:
        return MockProvider()
    try:
        return cls()
    except Exception:
        logger.exception("falling back to mock identity provider")
        return MockProvider()
