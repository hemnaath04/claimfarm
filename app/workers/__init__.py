"""Background-job abstraction.

The application code calls `submit(fn, *args, **kwargs)` and the worker
layer takes responsibility for actually running it — today on an in-process
thread pool, tomorrow on Alibaba MNS / Redis Queue / Celery without
touching the call sites.

Choose the backend via `JOB_BACKEND` env var: `inline` (synchronous, used
in tests) or `thread` (default).
"""

from app.workers.jobs import submit, JobBackend, get_backend

__all__ = ["submit", "JobBackend", "get_backend"]
