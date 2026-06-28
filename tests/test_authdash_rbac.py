"""RBAC regression tests for app/api_admin.py.

Verifies:
- Non-admin roles (moderator, reviewer, farmer) are blocked from every admin endpoint.
- Admins can suspend/unsuspend users and view the audit log.
- Admins CANNOT grant or revoke the owner role (privilege-escalation guard).
- Admins CANNOT change the role of another owner.
- Owners can promote/demote freely.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------- fixtures ----------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "rbac_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://testserver")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    from app import config
    from app.storage import db as db_module

    config.get_settings.cache_clear()
    db_module.get_engine.cache_clear()

    from app.main import app
    from app.middlewares import IPRateLimiter

    # The IPRateLimiter is a module-level singleton; all TestClient requests
    # share the same synthetic IP so the per-IP bucket fills up quickly when
    # tests run sequentially. Reset the hit table before each test.
    for mw in getattr(app, "user_middleware", []):
        instance = getattr(mw, "kwargs", {})
        # Middleware instances aren't directly accessible via user_middleware;
        # reach into the ASGI middleware stack instead.
        pass

    # Walk the ASGI stack to find the IPRateLimiter instance and clear it.
    asgi = app.middleware_stack
    while asgi is not None:
        if isinstance(asgi, IPRateLimiter):
            asgi._hits.clear()
            break
        asgi = getattr(asgi, "app", None)

    with TestClient(app) as c:
        yield c

    db_module.get_engine.cache_clear()
    config.get_settings.cache_clear()


def _sign_up(client: TestClient, email: str, password: str = "Hunter22A!") -> dict:
    r = client.post(
        "/auth/sign-up",
        json={"email": email, "password": password, "name": "Test"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def _force_role(user_id: str, role: str) -> None:
    """Directly write a role into the DB without going through the HTTP layer."""
    from app.storage import users_repo

    row = users_repo.get(user_id)
    assert row is not None
    row.role = role
    users_repo.upsert(row)


def _session_for(client: TestClient, email: str, password: str = "Hunter22A!") -> TestClient:
    """Sign in as a user and return the client with the session cookie set."""
    client.cookies.clear()
    r = client.post("/auth/sign-in", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return client


# ---------- helpers ----------

NON_ADMIN_ROLES = ["moderator", "reviewer", "farmer"]


# ---------- tests ----------

class TestNonAdminsBlocked:
    """Every admin endpoint must return 403 for non-owner/non-admin roles."""

    @pytest.mark.parametrize("role", NON_ADMIN_ROLES)
    def test_list_users_blocked(self, client, role):
        data = _sign_up(client, f"{role}@example.com")
        _force_role(data["user_id"], role)
        _session_for(client, f"{role}@example.com")
        r = client.get("/api/admin/users")
        assert r.status_code == 403, f"role={role}: expected 403 got {r.status_code}"

    @pytest.mark.parametrize("role", NON_ADMIN_ROLES)
    def test_suspend_user_blocked(self, client, role):
        # Create a victim user to suspend
        victim = _sign_up(client, f"victim-{role}@example.com")
        # Now create the actor with the non-admin role
        actor_data = _sign_up(client, f"actor-{role}@example.com")
        _force_role(actor_data["user_id"], role)
        _session_for(client, f"actor-{role}@example.com")
        r = client.post(f"/api/admin/users/{victim['user_id']}/suspend")
        assert r.status_code == 403, f"role={role}: expected 403 got {r.status_code}"

    @pytest.mark.parametrize("role", NON_ADMIN_ROLES)
    def test_audit_log_blocked(self, client, role):
        data = _sign_up(client, f"audit-{role}@example.com")
        _force_role(data["user_id"], role)
        _session_for(client, f"audit-{role}@example.com")
        r = client.get("/api/admin/audit")
        assert r.status_code == 403, f"role={role}: expected 403 got {r.status_code}"

    @pytest.mark.parametrize("role", NON_ADMIN_ROLES)
    def test_set_role_blocked(self, client, role):
        victim = _sign_up(client, f"setrole-victim-{role}@example.com")
        actor_data = _sign_up(client, f"setrole-actor-{role}@example.com")
        _force_role(actor_data["user_id"], role)
        _session_for(client, f"setrole-actor-{role}@example.com")
        r = client.post(f"/api/admin/users/{victim['user_id']}/role?role=reviewer")
        assert r.status_code == 403, f"role={role}: expected 403 got {r.status_code}"


class TestAdminCanOperate:
    """Admins can perform allowed operations."""

    def test_admin_can_list_users(self, client):
        data = _sign_up(client, "admin-list@example.com")
        _force_role(data["user_id"], "admin")
        _session_for(client, "admin-list@example.com")
        r = client.get("/api/admin/users")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_admin_can_suspend_and_unsuspend_non_owner(self, client):
        victim_data = _sign_up(client, "victim-suspend@example.com")
        # Set victim to reviewer so admin can suspend them
        _force_role(victim_data["user_id"], "reviewer")

        admin_data = _sign_up(client, "admin-suspend@example.com")
        _force_role(admin_data["user_id"], "admin")
        _session_for(client, "admin-suspend@example.com")

        r = client.post(f"/api/admin/users/{victim_data['user_id']}/suspend")
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is True

        r2 = client.post(f"/api/admin/users/{victim_data['user_id']}/unsuspend")
        assert r2.status_code == 200

    def test_admin_can_view_audit_log(self, client):
        data = _sign_up(client, "admin-audit@example.com")
        _force_role(data["user_id"], "admin")
        _session_for(client, "admin-audit@example.com")
        r = client.get("/api/admin/audit")
        assert r.status_code == 200
        assert "items" in r.json()

    def test_admin_can_change_non_owner_role(self, client):
        victim = _sign_up(client, "reviewer-for-change@example.com")
        _force_role(victim["user_id"], "reviewer")

        admin = _sign_up(client, "admin-changer@example.com")
        _force_role(admin["user_id"], "admin")
        _session_for(client, "admin-changer@example.com")

        r = client.post(f"/api/admin/users/{victim['user_id']}/role?role=moderator")
        assert r.status_code == 200, r.text


class TestAdminPrivilegeEscalationBlocked:
    """Admins cannot grant or revoke the owner role."""

    def test_admin_cannot_promote_to_owner(self, client):
        victim = _sign_up(client, "escalate-victim@example.com")
        _force_role(victim["user_id"], "reviewer")

        admin = _sign_up(client, "escalate-admin@example.com")
        _force_role(admin["user_id"], "admin")
        _session_for(client, "escalate-admin@example.com")

        r = client.post(f"/api/admin/users/{victim['user_id']}/role?role=owner")
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"

    def test_admin_cannot_change_owner_role(self, client):
        # An owner-role target cannot be touched by an admin.
        owner_target = _sign_up(client, "owner-target@example.com")
        # sign_up grants owner role by default, so user is already owner

        admin = _sign_up(client, "admin-touching-owner@example.com")
        _force_role(admin["user_id"], "admin")
        _session_for(client, "admin-touching-owner@example.com")

        r = client.post(f"/api/admin/users/{owner_target['user_id']}/role?role=reviewer")
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"

    def test_admin_cannot_suspend_owner(self, client):
        owner_target = _sign_up(client, "owner-suspend-target@example.com")
        # sign_up creates owners by default

        admin = _sign_up(client, "admin-who-tries-to-suspend-owner@example.com")
        _force_role(admin["user_id"], "admin")
        _session_for(client, "admin-who-tries-to-suspend-owner@example.com")

        r = client.post(f"/api/admin/users/{owner_target['user_id']}/suspend")
        assert r.status_code == 403, f"expected 403 got {r.status_code}: {r.text}"


class TestOwnerCanPromote:
    """Owners can grant the owner role to any user."""

    def test_owner_can_promote_to_owner(self, client):
        owner = _sign_up(client, "owner-promoter@example.com")
        # sign_up already creates as owner
        _session_for(client, "owner-promoter@example.com")

        target = _sign_up(client, "promotion-target@example.com")
        # sign-up gives target the owner role too, demote first
        _force_role(target["user_id"], "reviewer")
        # re-auth as owner (sign-up changes session cookie)
        _session_for(client, "owner-promoter@example.com")

        r = client.post(f"/api/admin/users/{target['user_id']}/role?role=owner")
        assert r.status_code == 200, r.text

    def test_owner_can_suspend_any_user(self, client):
        owner = _sign_up(client, "owner-suspender@example.com")
        _session_for(client, "owner-suspender@example.com")

        target = _sign_up(client, "suspend-any@example.com")
        # Re-auth as owner
        _session_for(client, "owner-suspender@example.com")

        r = client.post(f"/api/admin/users/{target['user_id']}/suspend")
        assert r.status_code == 200, r.text


class TestUnauthenticatedBlocked:
    """All admin endpoints require authentication."""

    def test_unauthenticated_list_users(self, client):
        client.cookies.clear()
        r = client.get("/api/admin/users")
        assert r.status_code == 401

    def test_unauthenticated_suspend(self, client):
        client.cookies.clear()
        r = client.post("/api/admin/users/usr_fake/suspend")
        assert r.status_code == 401

    def test_unauthenticated_audit(self, client):
        client.cookies.clear()
        r = client.get("/api/admin/audit")
        assert r.status_code == 401


class TestApiKeyOrgIsolation:
    """API key revoke must refuse keys belonging to another org."""

    def test_cannot_revoke_another_users_key(self, client):
        # User A issues a key
        a = _sign_up(client, "keya@example.com")
        _session_for(client, "keya@example.com")
        issued = client.post("/api/keys", json={"name": "a-key", "scope": "claims:read"})
        assert issued.status_code == 201
        key_id = issued.json()["key_id"]

        # User B signs up and tries to revoke user A's key
        _sign_up(client, "keyb@example.com")
        _session_for(client, "keyb@example.com")
        r = client.delete(f"/api/keys/{key_id}")
        assert r.status_code == 404, (
            f"expected 404 (key not in B's org) got {r.status_code}: {r.text}"
        )
