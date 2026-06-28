# ClaimFarm — User Action Required

Items that genuinely need the user (credentials, accounts, business decisions,
deploy approval). Each is isolated; all unrelated work continues without it.
Teammates append candidates; the lead curates this list.

---

## [ ] UAR-1 — Real email delivery (Resend API key)
- **What:** Set `RESEND_API_KEY` (+ verified `RESEND_FROM` domain) in FC env and Vercel is not needed.
- **Why:** Without it, sign-up verification / password-reset / magic-link emails are not delivered; the app falls back to dev-mode links returned in the API response. That fallback is intentional but not production email.
- **Steps:** Create a free account at https://resend.com → API Keys → create → add `RESEND_API_KEY=re_…` to the FC 3.0 function env (console → claimfarm-api → Environment Variables) → Save & Deploy. Optionally verify a sending domain and set `RESEND_FROM`.
- **Blocks:** True end-to-end email delivery tests (F-A04/F-A05 email leg).
- **Continue without:** Yes — dev-mode link flow is tested instead.
- **Security:** Keep the key only in FC env; never commit it.
- **Verify after:** Sign up a throwaway address; confirm an email arrives.

## [ ] UAR-2 — Payments provider (business decision + account)
- **What:** Decide on Paddle / LemonSqueezy / Razorpay (Stripe intentionally excluded — needs US SSN/business) and provide `PAYMENTS_PROVIDER` + keys.
- **Why:** Billing "Upgrade"/"Add payment method" cannot perform a real checkout without a provider. Until then the dashboard honestly shows the feature as unavailable (no fake button).
- **Steps:** Pick a provider, create an account, set `PAYMENTS_PROVIDER` + provider keys in FC env.
- **Blocks:** Real checkout (F-A10). 
- **Continue without:** Yes — UI is honestly labelled "provider not configured".
- **Security:** Provider keys in FC env only.
- **Verify after:** Upgrade flow opens the provider checkout.

## [ ] UAR-3 — Identity verification provider (optional)
- **What:** Provide Persona/Veriff/Onfido key + `IDENTITY_PROVIDER` if real KYC is wanted.
- **Why:** Identity verification runs in mock mode by default.
- **Blocks:** Real KYC (F-A16). **Continue without:** Yes (mock provider).

## [ ] UAR-4 — Telegram end-to-end test (test chat + safe crop image)
- **What:** A designated test Telegram account + a repo-owned crop image to exercise the live `/telegram/inbound` → claim flow on prod, without using a real farmer identity/location.
- **Why:** Lead/teammates must not message third parties or use real PII/location on prod.
- **Blocks:** Live prod Telegram E2E (F-C01..C18 prod leg). Local pipeline is fully tested instead.
- **Continue without:** Yes — pipeline verified locally with `data/eval/sample_drought_corn.jpg`.

## [ ] UAR-5 — Deploy/merge approval
- **What:** Confirm the lead may commit to `main` and let CI auto-deploy to FC + Vercel (CI auto-deploys on push per `.github/workflows`).
- **Why:** All fixes are made + verified locally; shipping requires pushing to `main`.
- **Steps:** Reply "push it" (or push yourself). 
- **Blocks:** Production rollout of the audit fixes.
- **Continue without:** Yes — everything is committed locally and verified; only the push/deploy is gated.
- **Verify after:** Lead reruns prod smoke after deploy.

## [ ] UAR-7 — Set TELEGRAM_WEBHOOK_SECRET (SEC-002)
- **What:** Generate a high-entropy string, set `TELEGRAM_WEBHOOK_SECRET` in FC env, AND pass it to Telegram `setWebhook(secret_token=…)`.
- **Why:** The Telegram webhook now validates `X-Telegram-Bot-Api-Secret-Token`. Until both the env var and the setWebhook secret are set, validation is skipped (dev mode) — meaning `/telegram/inbound` is forgeable.
- **Steps:** Pick a secret → FC env `TELEGRAM_WEBHOOK_SECRET=<secret>` → `curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" -d "url=<fc>/telegram/inbound" -d "secret_token=<secret>"`.
- **Blocks:** Hardened Telegram webhook (the validation code is shipped; it's inert until configured).
- **Continue without:** Yes — code is safe; this enables enforcement.

## [ ] UAR-8 — Set AUTH_DEV_LINKS=false + email in prod (SEC-007, Critical)
- **What:** The lead is flipping the code default to secure (`auth_dev_links=False`), so prod no longer leaks tokens. To restore the prod web sign-up/verify/reset email flow, configure `RESEND_API_KEY` (see UAR-1). Do NOT set `AUTH_DEV_LINKS=true` in production.
- **Why:** With dev-links on, `POST /auth/reset` returned a working reset link for any registered email = account takeover. Now off by default.
- **Steps:** Ensure FC env does NOT contain `AUTH_DEV_LINKS=true`; set `RESEND_API_KEY` to deliver real emails.
- **Blocks:** Prod web email-link flows until Resend is set (Telegram + local dev unaffected).
- **Continue without:** Yes — the security hole is closed by the code default; email delivery is the remaining convenience.

## [ ] UAR-6 — Rotate exposed credentials
- **What:** The Telegram bot token, Qwen key, Alibaba RAM key, and DashVector key have appeared in chat across sessions. Rotate them.
- **Why:** Hygiene — they may be cached.
- **Steps:** Telegram @BotFather /revoke + reissue; regenerate Qwen/DashVector keys; rotate the RAM AccessKey; update FC env with the new values.
- **Blocks:** Nothing functionally; security hygiene.
- **Verify after:** App still healthy with rotated keys.
