"""Pluggable background-job runner.

Two backends ship today:

- ``inline``: runs the callable synchronously in the caller's thread.
  Used in tests and in the rare case where ordering matters.

- ``thread``: pushes onto a process-wide ``ThreadPoolExecutor`` so
  request handlers return immediately. This is the default — it covers
  the FC 3.0 single-instance case where a Redis or MNS broker would be
  overkill, while keeping the call sites identical to the durable
  variant we'll swap in later.

To plug in a durable broker (Alibaba MNS, Redis Queue, Celery), add a
new ``JobBackend`` enum value, write an adapter that converts the call
into the broker's enqueue shape, and select it via ``JOB_BACKEND``. The
caller signature does not change.
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import Future, ThreadPoolExecutor
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


class JobBackend(str, Enum):
    inline = "inline"
    thread = "thread"


class _Runner(Protocol):
    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future: ...
    def shutdown(self, wait: bool) -> None: ...


class _InlineRunner:
    """Synchronous shim — useful in tests so assertions don't race."""

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
        f: Future = Future()
        try:
            result = fn(*args, **kwargs)
            f.set_result(result)
        except BaseException as exc:  # noqa: BLE001
            f.set_exception(exc)
        return f

    def shutdown(self, wait: bool) -> None:  # noqa: D401
        return


class _ThreadRunner:
    """Wraps ThreadPoolExecutor + logs unhandled exceptions instead of
    silently swallowing them like FastAPI's BackgroundTasks does on
    exception."""

    def __init__(self, max_workers: int) -> None:
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="cf-worker")

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
        future = self._pool.submit(fn, *args, **kwargs)
        future.add_done_callback(_log_failure)
        return future

    def shutdown(self, wait: bool) -> None:
        self._pool.shutdown(wait=wait)


def _log_failure(future: Future) -> None:
    exc = future.exception()
    if exc is not None:
        logger.exception("background job failed", exc_info=exc)


@lru_cache
def get_backend() -> _Runner:
    name = (os.environ.get("JOB_BACKEND") or JobBackend.thread.value).strip().lower()
    if name == JobBackend.inline.value:
        logger.info("workers: inline backend")
        return _InlineRunner()
    max_workers = int(os.environ.get("JOB_MAX_WORKERS", "4"))
    logger.info("workers: thread backend (max_workers=%d)", max_workers)
    return _ThreadRunner(max_workers=max_workers)


def submit(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Future:
    """Run ``fn(*args, **kwargs)`` on the active backend.

    The returned Future is fire-and-forget by convention. Callers that
    need a result must explicitly ``.result()`` it; everyone else can
    ignore the return value.
    """
    return get_backend().submit(fn, *args, **kwargs)


def shutdown(wait: bool = True) -> None:
    """Used by tests + clean shutdown hooks."""
    runner = get_backend()
    runner.shutdown(wait=wait)
    get_backend.cache_clear()
