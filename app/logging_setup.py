"""Structured logging.

Configures structlog to emit JSON in production and a human-friendly
console renderer in development. Stdlib `logging` is wired in so
existing `logger.info(...)` calls flow through unchanged.

Invoke `configure()` once at app startup.
"""

from __future__ import annotations

import logging
import os
import sys

import structlog


def configure(level: str = "INFO", *, json_output: bool | None = None) -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    use_json = json_output if json_output is not None else os.environ.get("LOG_FORMAT", "").lower() == "json"

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    renderer = (
        structlog.processors.JSONRenderer()
        if use_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
