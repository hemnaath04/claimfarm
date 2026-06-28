# ClaimFarm — QA Audit Final Report

**Date:** 2026-06-28 · **Lead:** engineering lead (main session) · **Team:** web-ux, auth-dashboard, claims-pipeline, api-security, verification

## 1. Production-readiness verdict

**Code is production-ready pending deploy + a short list of operational env settings.**
Not "fully production-ready" while BLOCKED — USER ACTION items remain (deploy
approval, prod email, webhook secrets). All repository-actionable defects are
fixed and verified locally; nothing actionable remains FAIL/TODO.

- **23 defects** found across 5 domains. **22 fixed and verified**, **1** (SEC-002 enforcement) is code-complete but inert until a secret is set (UAR-7).
- **3 Critical** (SEC-007 token disclosure / account-takeover, AUTH-003 privilege escalation, WUX-001 hero-blank) — all fixed + independently verified.
- **8 High** (AUTH-001/002, SEC-001/002/003/004, WUX-006/011, CLAIM-001) — all fixed + verified.
- Backend **98/98 tests pass**; frontend **tsc clean + build OK (19 routes)**.

## 2. What was fixed (by domain)

**Security (api-security + lead):**
- SEC-007 *Critical*: `AUTH_DEV_LINKS` defaulted true → prod echoed live verify/reset/magic tokens in JSON; `POST /auth/reset` with a victim's registered email returned a working reset link = account takeover. **Fixed: secure-by-default (False)** + 3 regression tests; local dev opts in via `.env`.
- SEC-001/002/003 *High*: Twilio/Telegram/Bird webhooks had no signature validation → forgeable intake. Added HMAC-SHA1 / secret-token / HMAC-SHA256 verification, 403 on failure.
- SEC-004 *High*: CORS preview-deploy regex matched `claimfarm-dashboard-evil.vercel.app`. Tightened to the Vercel hex-hash pattern; narrowed allowed methods.
- SEC-005/006/009/010 *Low*: stripped `Server` header, added HSTS, removed CI `|| true` (lint+tests now gate the build), narrowed CORS methods.

**Auth & dashboard (auth-dashboard):**
- AUTH-003 *Critical*: admin could promote any user to `owner` and suspend owners. Added owner-tier guards + 25 RBAC tests.
- AUTH-002 *High*: any authed user could revoke another org's API key (broken object-level authz). Added org-ownership check.
- AUTH-001 *High*: password-reset email linked to the API host (raw JSON page on FC). Fixed to frontend URL.
- AUTH-004 *Medium*: dashboard buttons silently no-op. Upgrade→`/api/billing/checkout` (or honest toast), Delete→`/api/me/delete` w/ confirm, non-functional controls disabled + labelled.
- CF-001 *Low*: ruff unused imports removed.

**Claims pipeline (claims-pipeline):**
- CLAIM-001 *High*: approve wrote `approved` before insurer submit → stuck-approved on insurer error. Now `submitted` preflight + rollback to `pending_review`.
- CLAIM-002 *Medium*: PDF never sent to farmer (read nonexistent field). Fixed.
- CLAIM-003 *Medium*: perceptual-hash dedupe existed but was never wired → duplicate claims. Wired into intake.
- CLAIM-004 *Low*: admin queue re-fetched on every click. CLAIM-005 *Medium*: 401 didn't redirect. Both fixed.

**Web UX (web-ux):**
- WUX-001 *Critical*: homepage hero blank on first paint (`animation-fill-mode: both` hid content during delay). Fixed to `forwards`.
- WUX-006 *High*: contact form POSTed to nonexistent `/api/contact` (404) → mailto fallback.
- WUX-011 *High*: no OpenGraph/Twitter metadata + thin SEO descriptions + 404 title bug. Added.
- WUX-MISC *Medium*: aria-label timing, mobile-nav `aria-controls`/`id`, logo aria-label.

**Lead (verification + cross-cutting):**
- VER-001 *Medium*: CLAIM-005 redirected to `/auth/login` (a 404). Corrected to `/auth/sign-in?next=/admin`.
- WUX-B01 *Low*: `turbopack.root` set in `next.config.ts` (workspace-root build warning gone).
- R-2 hardening: `tests/conftest.py` pins rate limit high so the now-blocking CI can't flake on 429.

## 3. Tests & builds that passed
- `uv run pytest` → **98 passed, 0 failed** (deterministic across runs).
- New regression tests: RBAC (25), webhooks (10), headers (12), claims (28), SEC-007 (3).
- `pnpm exec tsc --noEmit` clean; `pnpm build` → 19 routes, no warnings.
- Ruff clean (api-security confirmed; lead edits lint-clean).

## 4. Browser & API verification
- Frontend build green; web-ux captured before/after evidence for WUX-001 (see evidence/).
- API: anon → 401 on `/api/claims/*` (prod baseline confirmed); webhook 403 on bad signature (tests); CORS evil-subdomain rejected (tests).

## 5. Production verification
- Prod backend healthy at task start: `/healthz` 200, OpenAPI 31 paths, anon `/api/claims` **401**. Frontend routes 200.
- **Prod runs PRE-audit code** — the fixes are committed locally and verified locally but not yet deployed (deploy = push, which auto-triggers CI→FC+Vercel; gated on UAR-5). Post-deploy re-smoke required.

## 6. Remaining BLOCKED — USER ACTION (see USER_ACTION_REQUIRED.md)
- **UAR-5** Deploy/merge approval (push to main → CI auto-deploys).
- **UAR-1/UAR-8** `RESEND_API_KEY` for real prod email (until then prod web sign-up/verify/reset can't email; Telegram + local dev unaffected; security hole already closed by SEC-007 default).
- **UAR-7** `TELEGRAM_WEBHOOK_SECRET` (+ setWebhook secret) to *enforce* SEC-002 (code shipped, inert until set). Likewise `BIRD_WEBHOOK_SECRET`, `TWILIO_AUTH_TOKEN` for those channels.
- **UAR-2/UAR-3** Payments / identity providers (business decision) — UIs honestly labelled meanwhile.
- **UAR-6** Rotate credentials exposed in chat history.

## 7. Files changed (local, uncommitted)
Backend: `app/config.py`, `app/main.py`, `app/api_claims.py`, `app/middlewares.py`, `app/api_admin.py`, `app/api_keys_routes.py`, `app/auth/routes.py`, `app/auth/tokens.py`, `app/api_magic_link.py`, `app/agents/whatsapp_intake.py`, `.env.example`, `deploy/fc-env-vars.txt`, `.github/workflows/ci.yml`.
Frontend: `web/next.config.ts`, `web/src/app/dashboard/page.tsx`, `web/src/app/admin/page.tsx`, `web/src/lib/api.ts`, `web/src/app/layout.tsx`, `web/src/app/globals.css`, marketing pages, `site-header.tsx`, `brand/logo.tsx`, `theme-toggle.tsx`.
Tests: `tests/test_authdash_rbac.py`, `tests/test_apisec_webhooks.py`, `tests/test_apisec_headers.py`, `tests/test_claims_pipeline.py`, `tests/test_sec007_dev_links.py`, `tests/conftest.py`.
Audit: `qa-audit/**`.

## 8. Deployment/merge still required
Push `main` → GitHub Actions builds + deploys FC (backend) and Vercel (frontend). Then set UAR env vars in FC and re-run prod smoke. Gated on UAR-5.

## 9. Remaining risks
- R-1 prod-behind-local until deploy. R-2 rate-limit determinism (mitigated). R-3 FC `/tmp` SQLite ephemerality (demo-acceptable; durable DB is a separate decision).
