"""Sentry initializer — no-ops when SENTRY_DSN is unset.

The Sentry SDK is intentionally an *optional* runtime dependency. When
``SENTRY_DSN`` is empty (the dev + CI case) this module is a no-op so the
import surface stays trivial. In production, ship ``sentry-sdk`` and set
``SENTRY_DSN`` to start receiving events — no other code changes required.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_initialized = False


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Returns True if active."""
    global _initialized
    if _initialized:
        return True

    dsn = (os.environ.get("SENTRY_DSN") or "").strip()
    if not dsn:
        logger.debug("sentry: SENTRY_DSN unset, skipping")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logger.warning("sentry: SENTRY_DSN set but sentry-sdk is not installed")
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        release=os.environ.get("SENTRY_RELEASE") or None,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
        integrations=[FastApiIntegration(), StarletteIntegration()],
    )
    _initialized = True
    logger.info("sentry: initialized")
    return True


def capture_exception(exc: BaseException, **context: Any) -> None:
    """Safe to call when Sentry is not configured — it just no-ops."""
    if not _initialized:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for k, v in context.items():
                scope.set_extra(k, v)
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001
        logger.exception("sentry capture failed")
