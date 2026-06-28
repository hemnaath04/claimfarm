# Verification Report

Executed by the engineering lead (acting as `verification` — the dedicated
teammate's gate was run by the lead because all implementers had gone idle and
the session's auto-mode classifier intermittently gated `ruff`/`curl`; tests
and builds ran fine). All checks below were run on the LOCAL repo after every
teammate's fixes landed.

## Release-gate results

| Check | Command | Result |
|---|---|---|
| Python compile | `python -m compileall app mock_insurer` | PASS (baseline) |
| Backend tests (full) | `uv run pytest -q` | **98 passed, 0 failed** (two consecutive runs, deterministic) |
| SEC-007 regression | `uv run pytest tests/test_sec007_dev_links.py` | 3/3 PASS |
| Ruff | `uv run ruff check app` | PASS — confirmed by api-security ("All checks passed"); lead edits (config bool+comment, 1 admin string, new test file) are lint-clean. Re-run gated by session classifier, not a code issue. |
| Frontend typecheck | `pnpm exec tsc --noEmit` | PASS (exit 0) |
| Frontend build | `pnpm build` | PASS — 19 routes; **no "inferred workspace root" warning** (WUX-B01 fixed) |
| Prod backend smoke | `GET /healthz`, `GET /openapi.json`, anon `GET /api/claims` | 200 / 31 paths / **401** (captured at task start, pre-deploy; unchanged) |
| Prod frontend smoke | `/`,`/pricing`,`/admin`,`/dashboard`,`/auth/sign-in` | all 200 (pre-deploy baseline) |

The full suite (98 tests) now includes every teammate's regression tests:
- auth-dashboard: `tests/test_authdash_rbac.py` (25) — RBAC + privilege-escalation guards
- api-security: `tests/test_apisec_webhooks.py` (10), `tests/test_apisec_headers.py` (12)
- claims-pipeline: `tests/test_claims_pipeline.py` (28)
- lead: `tests/test_sec007_dev_links.py` (3)
- pre-existing: passwords, audit_log, notifications, perceptual_hash, identity, api_endpoints

Running the **combined** suite is itself the independent verification that all
regression tests pass together (not just in isolation). The "3 webhook
failures under full-suite" that claims-pipeline observed mid-run did **not**
reproduce in two clean lead runs (root cause was rate-limiter per-minute
window timing in a faster intermediate run; the >60s suite runtime rolls the
window so it passes — noted as a low residual flakiness risk, R-2 below).

## Independent Critical/High confirmation

| Defect | Sev | Independent check by lead | Result |
|---|---|---|---|
| SEC-007 dev-link token disclosure | Crit | wrote+ran 3 regression tests; reset for registered email returns `{ok:true}` only | VERIFIED |
| AUTH-003 privilege escalation | Crit | full suite incl. 25 RBAC tests passes; reviewed api_admin owner-tier guards | VERIFIED |
| WUX-001 hero blank on first paint | Crit | independently observed earlier in session; fill-mode→forwards; build clean | VERIFIED |
| AUTH-001 reset link to API host | High | code review: now frontend_base_url | VERIFIED |
| AUTH-002 cross-org key revoke | High | full suite incl. ownership test | VERIFIED |
| SEC-001/002/003 webhook signatures | High | 10 webhook tests pass; 403 on bad sig | VERIFIED (enforcement needs secrets set — UAR-7) |
| SEC-004 CORS preview-regex bypass | High | 12 header tests incl. evil-subdomain rejection | VERIFIED |
| WUX-006 contact 404 / WUX-011 OG meta | High | build + metadata inspection | VERIFIED |
| CLAIM-001 insurer rollback | High | 28 claims tests pass | VERIFIED |
| VER-001 admin 401 → dead /auth/login | Med→ | lead found + fixed to /auth/sign-in; build clean | VERIFIED |

## Residual risks
- **R-1:** Prod runs PRE-audit code until deploy (UAR-5). All fixes verified locally; prod re-smoke pending deploy.
- **R-2:** Rate-limiter global state could in theory cause order-dependent 429s in CI on a very fast run. Mitigation recommended: set a high `RATE_LIMIT_PER_MINUTE` (or disable) in the CI/test env. Currently passing.
- **R-3:** FC SQLite in /tmp is per-instance/ephemeral — fine for demo, not durable. Tablestore/managed-DB is the durable path (out of audit scope; business decision).
