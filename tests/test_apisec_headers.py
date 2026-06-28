"""Security tests: HTTP response headers and CORS policy.

Covers SEC-004 (CORS regex), SEC-005 (server header), SEC-006 (HSTS),
SEC-010 (allowed methods).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    from app.main import app

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# SEC-005: server header not disclosed
# ---------------------------------------------------------------------------

class TestServerHeader:
    def test_server_header_absent(self, client):
        resp = client.get("/healthz")
        assert "server" not in resp.headers


# ---------------------------------------------------------------------------
# SEC-006: HSTS present
# ---------------------------------------------------------------------------

class TestHSTS:
    def test_hsts_header_present(self, client):
        resp = client.get("/healthz")
        assert "strict-transport-security" in resp.headers
        sts = resp.headers["strict-transport-security"]
        assert "max-age=" in sts
        # At least 6 months
        max_age = int(sts.split("max-age=")[1].split(";")[0].strip())
        assert max_age >= 15_552_000


# ---------------------------------------------------------------------------
# SEC-004: CORS regex tightness
# ---------------------------------------------------------------------------

class TestCORSRegex:
    """Verify that the origin allowlist does not grant credentials to
    arbitrary *.vercel.app subdomains that start with our project name."""

    def _preflight(self, client, origin: str) -> dict:
        resp = client.options(
            "/api/claims",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        return {
            "status": resp.status_code,
            "allow_origin": resp.headers.get("access-control-allow-origin", ""),
            "allow_creds": resp.headers.get("access-control-allow-credentials", ""),
        }

    def test_canonical_origin_allowed(self, client):
        r = self._preflight(client, "https://claimfarm-dashboard.vercel.app")
        assert r["allow_origin"] == "https://claimfarm-dashboard.vercel.app"
        assert r["allow_creds"] == "true"

    def test_evil_suffix_origin_blocked(self, client):
        """An attacker-controlled vercel project named 'claimfarm-dashboard-evil'
        must NOT receive credentials.  SEC-004 regression."""
        r = self._preflight(client, "https://claimfarm-dashboard-evil.vercel.app")
        # No reflected origin with credentials
        assert not (
            r["allow_origin"] == "https://claimfarm-dashboard-evil.vercel.app"
            and r["allow_creds"] == "true"
        )

    def test_unrelated_origin_blocked(self, client):
        r = self._preflight(client, "https://evil.com")
        assert r["allow_origin"] != "https://evil.com"

    def test_localhost_allowed(self, client):
        r = self._preflight(client, "http://localhost:3000")
        assert r["allow_origin"] == "http://localhost:3000"


# ---------------------------------------------------------------------------
# SEC-010: allowed methods
# ---------------------------------------------------------------------------

class TestAllowedMethods:
    def test_only_safe_methods_listed(self, client):
        resp = client.options(
            "/api/claims",
            headers={
                "Origin": "https://claimfarm-dashboard.vercel.app",
                "Access-Control-Request-Method": "DELETE",
            },
        )
        allowed = resp.headers.get("access-control-allow-methods", "")
        # DELETE and PATCH should not appear in the CORS-allowed method list.
        assert "DELETE" not in allowed
        assert "PATCH" not in allowed


# ---------------------------------------------------------------------------
# General: other OWASP headers
# ---------------------------------------------------------------------------

class TestOWASPHeaders:
    REQUIRED = {
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff",
        "referrer-policy": "no-referrer",
    }

    def test_owasp_headers_present(self, client):
        resp = client.get("/healthz")
        for header, expected in self.REQUIRED.items():
            assert resp.headers.get(header) == expected, (
                f"Header {header!r} expected {expected!r}, got {resp.headers.get(header)!r}"
            )

    def test_csp_present(self, client):
        resp = client.get("/healthz")
        assert "content-security-policy" in resp.headers

    def test_no_cache_on_api_routes(self, client):
        """All /api/* responses must carry Cache-Control: no-store."""
        # 401 response from an unauthed request still carries cache headers.
        resp = client.get("/api/claims")
        cc = resp.headers.get("cache-control", "")
        assert "no-store" in cc


# ---------------------------------------------------------------------------
# Auth: unauthed requests get 401, not 403 or 500
# ---------------------------------------------------------------------------

class TestAuthRequirement:
    PROTECTED = [
        "/api/claims",
        "/api/claims/nonexistent",
        "/api/claims/x/localized_reply",
        "/api/admin/users",
        "/api/admin/audit",
        "/api/me/export",
        "/api/keys",
    ]

    def test_unauthenticated_returns_401(self, client):
        for path in self.PROTECTED:
            resp = client.get(path)
            assert resp.status_code == 401, (
                f"Expected 401 on {path}, got {resp.status_code}"
            )

    def test_post_decision_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/api/claims/x/decision",
            json={"decision": "approve"},
        )
        assert resp.status_code == 401
