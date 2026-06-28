"""HTTP middlewares: rate limiting, security headers."""

from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class IPRateLimiter(BaseHTTPMiddleware):
    """Per-IP token-bucket-ish limiter for /api/* and /auth/* endpoints.

    Defaults: 60 requests / IP / minute. Tuned for hackathon scale; real
    deployments should front the app with a CDN (Vercel Edge / Cloudflare
    WAF / API Gateway) that implements proper distributed rate limiting.
    """

    def __init__(
        self,
        app,
        *,
        rate: int = 60,
        window_seconds: int = 60,
        protected_prefixes: tuple[str, ...] = ("/api/", "/auth/"),
    ) -> None:
        super().__init__(app)
        self.rate = rate
        self.window = window_seconds
        self.protected = protected_prefixes
        self._hits: dict[str, deque[float]] = {}
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if not any(path.startswith(p) for p in self.protected):
            return await call_next(request)

        ip = request.client.host if request.client else "anon"
        now = time.monotonic()

        with self._lock:
            dq = self._hits.setdefault(ip, deque())
            # Drop expired entries
            while dq and (now - dq[0]) > self.window:
                dq.popleft()
            if len(dq) >= self.rate:
                return JSONResponse(
                    {"detail": "rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": str(self.window)},
                )
            dq.append(now)

        return await call_next(request)


class SecurityHeaders(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        # Don't override headers callers explicitly set.
        h = response.headers
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("Referrer-Policy", "no-referrer")
        h.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        # CSP is intentionally loose — production should tighten when the
        # marketing surface is finalized (the Next.js admin needs inline
        # styles for shadcn at build time).
        h.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "connect-src 'self' https: wss:; font-src 'self' data: https:; "
            "frame-ancestors 'none'",
        )
        # SEC-006: HSTS — only meaningful over HTTPS (the FC / Vercel edge
        # always terminates TLS before us), but harmless on HTTP and correct
        # in prod.  max-age=31536000 = 1 year; includeSubDomains excluded
        # because we share *.fcapp.run with other tenants.
        h.setdefault("Strict-Transport-Security", "max-age=31536000")
        # SEC-005: Remove the default "server: uvicorn" disclosure header.
        if "server" in h:
            del h["server"]
        return response
