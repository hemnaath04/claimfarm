# ClaimFarm — Feature Inventory & Coverage Matrix

Lead-owned. Each teammate fills the `Local`, `Prod`, `Tests`, `Class`, `Evidence`
columns for their domain. Classifications: **PASS** (verified pass),
**FIXED** (fixed and verified), **BLOCKED** (user action), **N/A**.

Baseline (captured by lead, 2026-06-28):
- Prod backend `/healthz` 200, OpenAPI 31 paths, `/api/claims` anon → **401** (auth gate live).
- Prod frontend `/`, `/pricing`, `/admin`, `/dashboard`, `/auth/sign-in` → 200.
- Backend: `compileall` OK, **pytest 20/20**, ruff **3 errors** (unused imports) → DEFECT CF-001.
- Working tree clean; all commits pushed; CI auto-deploys to FC on push.

## Owner legend
web-ux (UX), auth-dashboard (AUTH), claims-pipeline (CLAIM), api-security (API), verification (VER).

| ID | Feature | Surface | Route/Endpoint | Owner | Class |
|----|---------|---------|----------------|-------|-------|
| F-W01 | Homepage hero + sections + motion | web | `/` | UX | |
| F-W02 | Pricing (plans, recommended pill) | web | `/pricing` | UX | |
| F-W03 | About | web | `/about` | UX | |
| F-W04 | FAQ accordion | web | `/faq` | UX | |
| F-W05 | Blog index | web | `/blog` | UX | |
| F-W06 | Blog article(s) | web | `/blog/[slug]` | UX | |
| F-W07 | Contact (form + channels) | web | `/contact` | UX | |
| F-W08 | Farmer landing | web | `/farmer` | UX | |
| F-W09 | Legal terms | web | `/legal/terms` | UX | |
| F-W10 | Legal privacy | web | `/legal/privacy` | UX | |
| F-W11 | 404 not-found | web | unknown route | UX | |
| F-W12 | Route error boundary | web | error.tsx/global-error | UX | |
| F-W13 | Header + mobile nav + theme toggle | web | all | UX | |
| F-W14 | Footer | web | all | UX | |
| F-W15 | Light/dark theme tokens | web | all | UX | |
| F-W16 | Responsive (mobile/tablet/desktop) | web | all | UX | |
| F-W17 | SEO metadata + favicon/og | web | all | UX | |
| F-A01 | Sign-up (validation, conflict) | auth | `/auth/sign-up`, POST /auth/sign-up | AUTH | |
| F-A02 | Sign-in (friendly errors, next=) | auth | `/auth/sign-in`, POST /auth/sign-in | AUTH | |
| F-A03 | Sign-out | auth | POST /auth/sign-out | AUTH | |
| F-A04 | Password reset (req+confirm) | auth | `/auth/reset`, POST /auth/reset(/confirm) | AUTH | |
| F-A05 | Email verify (token, redirect) | auth | `/auth/verify`, GET /auth/verify | AUTH | |
| F-A06 | Magic link (request+consume) | auth | POST /auth/magic-link, GET consume | AUTH | |
| F-A07 | Session cookie flags (SameSite/Secure) | auth | cookie | AUTH | |
| F-A08 | Protected-route gate (console) | auth | `/dashboard`,`/admin` | AUTH | |
| F-A09 | Dashboard Overview (stats) | auth | `/dashboard` | AUTH | |
| F-A10 | Dashboard Billing (provider-disabled) | auth | `/dashboard` | AUTH | |
| F-A11 | Dashboard Team list | auth | `/dashboard` | AUTH | |
| F-A12 | API keys issue/list/revoke | auth | `/api/keys` | AUTH | |
| F-A13 | Webhooks panel | auth | `/dashboard` | AUTH | |
| F-A14 | Notification prefs | auth | `/dashboard` | AUTH | |
| F-A15 | Workspace settings + danger zone | auth | `/dashboard` | AUTH | |
| F-A16 | Identity verification | auth | `/api/identity/*` | AUTH | |
| F-A17 | Admin user mgmt (roles/suspend) | auth | `/api/admin/*` | AUTH | |
| F-A18 | RBAC role→action matrix | auth | API | AUTH | |
| F-A19 | GDPR export/delete | auth | `/api/me/*` | AUTH | |
| F-C01 | Telegram /start onboarding | claim | POST /telegram/inbound | CLAIM | |
| F-C02 | Location collection | claim | telegram | CLAIM | |
| F-C03 | Photo intake + persist + serve | claim | telegram, GET /api/claims/{id}/photo | CLAIM | |
| F-C04 | Damage assessment (Qwen-VL) | claim | agents/damage_assessor | CLAIM | |
| F-C05 | Weather corroboration | claim | agents/weather_corroborator | CLAIM | |
| F-C06 | Photo forensics + EXIF | claim | agents/photo_forensics | CLAIM | |
| F-C07 | Perceptual hash + duplicate | claim | clients/perceptual_hash | CLAIM | |
| F-C08 | Fraud detection | claim | agents/fraud_check | CLAIM | |
| F-C09 | Agronomy retrieval | claim | agents/agronomy_rag | CLAIM | |
| F-C10 | Similar-claim retrieval | claim | agents/past_claim_rag | CLAIM | |
| F-C11 | Multilingual replies | claim | agents/multilingual | CLAIM | |
| F-C12 | Claim drafting | claim | agents/claim_drafter | CLAIM | |
| F-C13 | PDF generation | claim | clients/pdf (WeasyPrint) | CLAIM | |
| F-C14 | Adjuster console queue+filters | claim | `/admin`, GET /api/claims | CLAIM | |
| F-C15 | Claim detail panels | claim | `/admin`, GET /api/claims/{id} | CLAIM | |
| F-C16 | Adjuster decision | claim | POST /api/claims/{id}/decision | CLAIM | |
| F-C17 | Mock insurer submission | claim | clients/insurer, /insurer/* | CLAIM | |
| F-C18 | Farmer decision notification | claim | telegram | CLAIM | |
| F-S01 | /healthz, /docs, /openapi.json | api | root | API | |
| F-S02 | Auth enforcement on claims API | api | /api/claims/* | API | |
| F-S03 | Admin API authz | api | /api/admin/* | API | |
| F-S04 | Identity/billing API authz | api | /api/identity,/api/billing | API | |
| F-S05 | Telegram webhook validation | api | /telegram/inbound | API | |
| F-S06 | Twilio/Bird webhooks | api | /twilio,/bird/inbound | API | |
| F-S07 | CORS policy | api | all | API | |
| F-S08 | Rate limiting | api | all | API | |
| F-S09 | Security headers | api | all | API | |
| F-S10 | Input validation + error shape | api | all | API | |
| F-S11 | Sensitive-data exposure | api | all | API | |
| F-S12 | Config/env + deploy consistency | api | Dockerfile/CI | API | |
| F-V01 | Existing pytest suite | test | tests/ | VER | |
| F-V02 | Frontend tsc + build | test | web | VER | |
| F-V03 | Production smoke (all routes) | test | prod | VER | |
| F-V04 | Accessibility checks | test | web | VER | |
| F-V05 | Responsive checks | test | web | VER | |
| F-V06 | Coverage matrix maintenance | test | this file | VER | |

## Final classifications (all items)

Detail per feature is in the owning teammate's report. Summary:

**Web (F-W01–W17):** all **VERIFIED PASS** except — F-W01 **FIXED** (WUX-001 hero-blank), F-W07 **FIXED** (WUX-006 contact 404→mailto), F-W17 **FIXED** (WUX-011 OG/SEO + WUX-B01 build warning), F-W04/W13 **FIXED** (WUX-MISC a11y). Live prod re-verify of these is post-deploy (UAR-5).

**Auth/Dashboard (F-A01–A19):** **VERIFIED PASS** except — F-A04 **FIXED** (AUTH-001 reset URL), F-A12 **FIXED** (AUTH-002 cross-org revoke), F-A17/A18 **FIXED** (AUTH-003 privilege escalation + RBAC matrix), F-A10 **FIXED+partly BLOCKED** (Upgrade wired; real checkout BLOCKED UAR-2), F-A15 **FIXED** (controls wired/labelled), F-A16 **N/A→mock** (real KYC BLOCKED UAR-3), F-A05/A06 email leg **BLOCKED** (UAR-1/UAR-8 email; flows themselves PASS via token/dev path).

**Claims (F-C01–C18):** **VERIFIED PASS** (local, with real creds + sample image) except — F-C16 **FIXED** (CLAIM-001 rollback), F-C18 **FIXED** (CLAIM-002 PDF), F-C07 **FIXED** (CLAIM-003 dedupe wired), F-C14 **FIXED** (CLAIM-004/005 + VER-001). Live prod Telegram E2E **BLOCKED** (UAR-4 test account/safe image).

**API/Security (F-S01–S12):** **VERIFIED PASS** except — F-S05/S06 **FIXED** (SEC-001/002/003 webhook signatures; enforcement BLOCKED on secrets UAR-7), F-S07 **FIXED** (SEC-004 CORS), F-S09 **FIXED** (SEC-005/006), F-S11 **FIXED** (SEC-007 token disclosure), F-S12 **FIXED** (SEC-009 CI gating). 

**Verification (F-V01–V06):** **VERIFIED PASS** — 98/98 backend, tsc+build clean, prod baseline smoke, coverage matrix maintained.

No remaining FAIL / TODO / UNINVESTIGATED. All non-PASS items are FIXED+verified locally or BLOCKED — USER ACTION (enumerated in USER_ACTION_REQUIRED.md).

## Known defects (seed)
- **CF-001** (Low): ruff F401 unused imports — FIXED (auth-dashboard).
