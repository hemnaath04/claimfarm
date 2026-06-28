# Auth-Dashboard Audit Report

**Agent:** auth-dashboard  
**Date:** 2026-06-28  
**Scope:** app/auth/\*, app/api_magic_link.py, app/api_keys_routes.py, app/storage/api_keys.py, app/api_identity.py, app/api_gdpr.py, app/api_admin.py, app/api_billing.py, app/models/user.py, web/src/app/auth/\*\*, web/src/app/dashboard/page.tsx, web/src/components/app/app-shell.tsx, web/src/lib/user-state.ts, web/src/lib/auth-fetch.ts

---

## Summary

| Category | Status |
|---|---|
| Lint (CF-001) | FIXED |
| Auth flows | PASS (minor fix) |
| Protected-route gate | PASS |
| Dashboard controls | FIXED |
| API keys | PASS + org-isolation fix |
| Identity / GDPR | PASS |
| RBAC + Admin API | FIXED + tests added |

---

## Defects Found and Fixed

### CF-001 — Unused Imports (Lint)
**Severity:** low  
**Files:** `app/api_magic_link.py`, `app/auth/tokens.py`

- `app/api_magic_link.py:16` — `datetime.datetime` imported but unused (only `timedelta` needed).
- `app/api_magic_link.py:23` — `SESSION_COOKIE` imported from `app.auth.routes` but unused in this module (only `_set_session_cookie` and `html_redirect` are used).
- `app/auth/tokens.py:18` — `sqlmodel.select` imported but unused.

**Fix:** Removed all three. `uv run ruff check app/auth app/api_magic_link.py` is now clean.

---

### AUTH-001 — Password-Reset Link Points at API, Not Frontend
**Severity:** high  
**File:** `app/auth/routes.py:204`

`reset_request` built the reset URL using `settings.public_base_url` (the FastAPI backend URL, e.g. `https://claimfarm-api-*.fcapp.run/auth/reset/confirm?token=…`). Function Compute's default domain cannot serve HTML. The user would land on raw JSON instead of the styled reset-confirmation page.

**Evidence:** Line 204 used `settings.public_base_url.rstrip("/")` while the immediately adjacent email-verification URL on sign-up (line 128) correctly used `settings.frontend_base_url`.

**Fix:** Changed to `settings.frontend_base_url` — consistent with the sign-up and magic-link flows.

---

### AUTH-002 — API Key Revoke Has No Org-Isolation Check
**Severity:** high  
**File:** `app/api_keys_routes.py:79-85`

`DELETE /api/keys/{key_id}` called `api_keys.revoke(key_id)` without verifying the key belongs to the authenticated user's org. Any authenticated user could revoke any other organization's API keys by guessing or leaking a `key_id`.

**Fix:** Fetch `list_for_org(org_id)` first; 404 if the key_id is not in the caller's org. The subsequent `revoke()` call then only runs when ownership is confirmed.

**Test:** `TestApiKeyOrgIsolation::test_cannot_revoke_another_users_key` in `tests/test_authdash_rbac.py`.

---

### AUTH-003 — Admin Can Escalate Privileges (No Owner-Role Guard)
**Severity:** critical  
**File:** `app/api_admin.py`

`set_role` let any `admin`-role user promote any other user to `owner`. This is a privilege-escalation path: a compromised admin account could promote itself or an accomplice to owner.

Additionally, `suspend_user` let admins suspend owner-role users, and the `_require_admin` return type was `str` but callers needed the role too, forcing them to re-query the DB or work blind.

**Fix:**
- `_require_admin` now returns `(user_id, role)` tuple — no extra DB queries needed.
- `set_role`: if `new_role == owner` and `actor_role != owner` → 403.
- `set_role`: if target user is an `owner` and caller is not an `owner` → 403.
- `suspend_user`: if target is an `owner` and caller is not an `owner` → 403.
- Fixed `audit_log_tail` signature from `request: Request = None` (default None is unsound) to `*, request: Request` (keyword-only, required).

**Tests:** `TestAdminPrivilegeEscalationBlocked` (3 tests) + `TestOwnerCanPromote` (2 tests) in `tests/test_authdash_rbac.py`.

---

### AUTH-004 — Dashboard Buttons Silently Do Nothing
**Severity:** high  
**File:** `web/src/app/dashboard/page.tsx`

Multiple controls looked interactive but had no effect:

| Control | Before | After |
|---|---|---|
| "Upgrade to Growth" | `<Button>` with no onClick | Calls `POST /api/billing/checkout?plan=growth`; follows redirect to payment provider; shows toast if provider unconfigured |
| "Add payment method" | `<Button variant="outline" disabled>` with misleading label including tech detail | `disabled` + `DisabledNote` explaining it's managed by payment provider during checkout |
| "Invite member" | Active-looking `<Button>` with no onClick | `disabled` + `DisabledNote` explaining the limitation |
| Webhook URL input + "Add another" | Non-disabled input; non-disabled button | Both `disabled`; `DisabledNote` explaining webhooks are not yet configurable |
| Settings fields (name, region, tz) | Non-disabled inputs | `disabled` + `DisabledNote` |
| "Delete workspace" | Active-looking `<Button variant="destructive">` with no onClick | Wired to `POST /api/me/delete`; two-click confirmation; redirects to `/` after deletion |
| Notification switches | Local state only | Local state with honest note that server-side persistence is coming |

Also: header greeting now uses the authenticated user's name via `useAuthUser()` instead of hardcoded `"Demo NGO"`.

---

## RBAC Matrix

| Role | List users | Suspend user | Unsuspend user | Change role | Suspend owner | Promote to owner | View audit log |
|---|---|---|---|---|---|---|---|
| **owner** | yes | yes | yes | yes | yes | yes | yes |
| **admin** | yes | yes (non-owner) | yes | yes (non-owner, non-→owner) | **no** | **no** | yes |
| **moderator** | **no** | **no** | **no** | **no** | **no** | **no** | **no** |
| **reviewer** | **no** | **no** | **no** | **no** | **no** | **no** | **no** |
| **farmer** | **no** | **no** | **no** | **no** | **no** | **no** | **no** |

**Enforcement point:** `app/api_admin.py` — `_require_admin()` + per-endpoint owner checks.  
**Test coverage:** `tests/test_authdash_rbac.py` — 25 tests covering all rows and the privilege-escalation boundary.

---

## Feature Classification (Fully Working)

| Feature | Classification | Notes |
|---|---|---|
| Sign-up (dup email 409, weak pw) | PASS | EmailStr + `Field(min_length=8)` enforced; 409 is friendly |
| Sign-in (wrong pw, unknown account) | PASS | Generic 401 "invalid credentials" — no enumeration |
| Sign-out | PASS | Session deleted server-side + cookie cleared |
| Password reset request | PASS (after fix) | Always-200; no enumeration; reset_url now points at frontend |
| Password reset confirm | PASS | Token single-use, 1h expiry, argon2id rehash |
| Email verify (valid/invalid/expired/reused) | PASS | Returns `{status: "ok"|"expired"|"unknown"}`; consumed_at guards reuse |
| Magic-link request | PASS | Always-200; single-use 15min token; dev-mode link fallback |
| Magic-link consume | PASS | Single-use; marks email_verified; creates session; html_redirect |
| Cookie flags | PASS | `SameSite=None+Secure` on HTTPS; `Lax` on HTTP localhost; `HttpOnly` |
| Protected-route gate (app-shell) | PASS | `useAuthUser` → `user===false` triggers redirect; children don't render |
| API keys issue/list/revoke | PASS (after fix) | One-time secret reveal; SHA-256 stored; org-isolated revoke |
| Identity (start/result) | PASS | Auth required; user_id scoped; mock provider returns deterministic results |
| GDPR export | PASS | Auth required; user-scoped; `Content-Disposition: attachment` |
| GDPR delete | PASS | Soft-delete + session revoke; wire from dashboard ✓ |
| Admin list users | PASS | owner+admin only |
| Admin suspend/unsuspend | PASS | owner+admin; admin blocked from suspending owners |
| Admin set role | PASS | Escalation to owner gated to owner-only |
| Admin audit log | PASS | owner+admin only |
| Billing checkout | PASS (wire only) | Calls backend; shows honest toast when provider unconfigured |
| Billing webhook | PASS | HMAC check delegated to provider adapter; `none` provider skips |

---

## BLOCKED — USER ACTION Required

| Item | Why |
|---|---|
| Real email delivery (verify, reset, magic-link) | `RESEND_API_KEY` or `SENDGRID_API_KEY` not set. Dev-mode links returned in JSON response as fallback. |
| Billing checkout redirect | `PAYMENTS_PROVIDER` not set. `POST /api/billing/checkout` returns `{"url": "stub"}`. Set `PAYMENTS_PROVIDER=paddle` (or `lemonsqueezy` / `razorpay`) + credentials to enable real checkout. |
| Identity verification real provider | `IDENTITY_PROVIDER=mock`. Set to `persona`, `veriff`, or `onfido` + API key for real IDV. |
| Webhook management UI | No backend webhook endpoint management API exists. Needs a new `webhooks_routes.py` (out of scope for this sprint). |
| Notification preferences persistence | No API endpoint for storing notification prefs. Switches are local-state only. Needs a new endpoint (out of scope). |
| Team invitations | No invite-member API exists. Needs new endpoint (out of scope). |
| Workspace settings save | No API for updating org name/region/tz. Needs new endpoint (out of scope). |

---

## Files Changed

### Backend
- `app/api_magic_link.py` — removed unused `datetime` + `SESSION_COOKIE` imports
- `app/auth/tokens.py` — removed unused `select` import
- `app/auth/routes.py` — reset URL now uses `frontend_base_url` (not `public_base_url`)
- `app/api_keys_routes.py` — revoke endpoint checks org ownership before revoking
- `app/api_admin.py` — RBAC: privilege-escalation guard; owner-suspension guard; `_require_admin` returns role; signature fix on `audit_log_tail`

### Frontend
- `web/src/app/dashboard/page.tsx` — Upgrade wired to billing API; Delete Account wired to GDPR delete; disabled controls labeled honestly; greeting uses real user name

### Tests (new)
- `tests/test_authdash_rbac.py` — 25 tests covering RBAC matrix, privilege escalation, unauthenticated access, and API key org isolation

---

## Test Results

```
tests/test_authdash_rbac.py    25 passed
tests/test_api_endpoints.py     5 passed
tests/test_passwords.py         3 passed
tests/test_audit_log.py         3 passed
pnpm exec tsc --noEmit          clean (no errors)
uv run ruff check app/auth app/api_magic_link.py   clean
```
