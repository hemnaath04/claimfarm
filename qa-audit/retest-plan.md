# ClaimFarm — Retest Plan

After each fix lands, the owner runs focused tests; `verification` runs the
release gate. Order of execution at the gate:

## Backend
1. `uv run python -m compileall -q app mock_insurer`
2. `uv run ruff check app` → 0 errors
3. `uv run pytest -q` → all pass
4. Local uvicorn smoke: anon `/api/claims` → 401; signed-in → 200; webhooks → 200.

## Frontend
5. `cd web && pnpm exec tsc --noEmit`
6. `cd web && pnpm build` → 18 routes
7. pixelshot key routes @ 390/768/1440 → no overflow, no console errors.

## Production smoke (read-only)
8. `/healthz` 200; `/openapi.json` path count; anon `/api/claims` 401.
9. Frontend routes 200: `/ /pricing /about /faq /blog /contact /farmer /legal/terms /legal/privacy /auth/sign-in /auth/sign-up /auth/reset /auth/verify /dashboard /admin` + unknown→404.

## Per-defect retest
For each defect in defects.json: independent repro (before) → fix → focused test → full suite → independent verify (after) → nearby-regression check. Critical/High require `verification` independent before+after evidence.

## Auth/RBAC
10. Edge cases: dup email 409, weak pw, bad pw 401, reset/verify token states, magic-link single-use.
11. RBAC matrix: non-owner blocked from admin actions (server-side), proven by tests.

## Claims pipeline
12. Local end-to-end with `data/eval/sample_drought_corn.jpg`: assess→forensics→weather→fraud→draft→pdf→save; decision→insurer→notify (insurer/notify failure tolerated).
