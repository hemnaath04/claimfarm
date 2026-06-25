# Security considerations + threat model

This is a living document. It covers how ClaimFarm thinks about each
class of risk, what's implemented today, and what's still open. The
goal is to be honest about both — not to oversell hardening that hasn't
been done.

---

## Identity and trust boundaries

| Boundary | Trust level | Defences |
|---|---|---|
| **Public landing pages** (`/`, `/pricing`, `/about`, ...) | Public | Read-only; static rendering on Vercel; standard headers |
| **Authenticated dashboard** (`/admin`, `/dashboard`) | Per-user | Server-side session cookie, role-gated API routes |
| **JSON API** (`/api/*`) | Per-user (via cookie) | Rate-limited, role-gated where required, no-store responses |
| **Channel webhooks** (`/telegram/inbound`, etc.) | Public but signed | Provider signature where available (Telegram secret token, Stripe sig) |
| **Internal insurer** (`/insurer/*`) | Internal (loopback) | Mounted as sub-app; real deployments replace this with the carrier's API |

---

## Implemented controls (OWASP Top 10 cross-reference)

### A01: Broken access control
- 5-tier RBAC (`owner > admin > moderator > reviewer > farmer`), gated server-side in `app/api_admin.py` and `app/api_identity.py`
- Sessions are opaque server-side tokens; logout immediately invalidates
- Role escalation requires an existing admin call

### A02: Cryptographic failures
- Passwords: PBKDF2-HMAC-SHA256, 600k iterations, 16-byte salt (OWASP 2023 minimum)
- Sessions: `secrets.token_urlsafe(32)` random tokens
- One-time tokens (verify email, reset password): same generator, explicit expiry
- TLS at Vercel + FC edges; HTTPS-only cookies in production (auto-detected from `PUBLIC_BASE_URL`)
- Photos + PDFs stored in OSS with server-side encryption + signed URLs

### A03: Injection
- All DB access via SQLModel (parameterised) — no raw SQL string concatenation
- HTML escaped by Jinja in PDF templates (`autoescape=select_autoescape`)
- JSON payload validation via Pydantic on every endpoint
- Subprocess and shell calls limited to dev-only scripts

### A04: Insecure design
- Identity verification is layered (EXIF + Qwen-VL authenticity + perceptual hash + provider KYC)
- Fraud detection is layered (same-farmer near-dup + cross-farmer narrative reuse + behavioral)
- Mock insurer simulates rejection scenarios so the happy path isn't the only tested path

### A05: Security misconfiguration
- `SecurityHeaders` middleware: `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`, baseline CSP
- `.env` is gitignored; `.env.example` enumerates every key
- Docker image runs as non-root user — TODO (currently runs as root, see "Open items")

### A06: Vulnerable + outdated components
- uv lock file pins every dependency
- pnpm lock file pins every JS dependency
- CI runs on every push to `main` (`.github/workflows/ci.yml`)
- Dependabot — TODO

### A07: Identification + authentication failures
- Password minimum 8 chars (UI-enforced + pydantic-validated)
- Always-200 reset endpoint to avoid email enumeration
- Email verification before sensitive actions (TODO: enforce on claim filing)
- Brute-force protection via per-IP rate limiter

### A08: Software + data integrity failures
- Stripe webhook signature verified in `parse_webhook` when `STRIPE_WEBHOOK_SECRET` is set
- Telegram updates verified via the bot token in the path
- Container images built reproducibly via GitHub Actions; deploys reference image by SHA, not `:latest`

### A09: Security logging + monitoring failures
- `audit_log.record(...)` called for every state change (sign-up, sign-in, sign-out, IDV start/result, billing webhook, admin actions, suspend, role change)
- Append-only JSONL log at `/tmp/claimfarm_audit.jsonl`; production swaps to Tablestore

### A10: Server-side request forgery
- Outbound URLs are constants (Open-Meteo, Qwen, Twilio/Bird/Telegram) — no user-controlled URL fetches
- Media downloads from messaging providers use authenticated API helpers, not raw URL pass-through

---

## Anti-fraud — layered

| Layer | What it catches | Where |
|---|---|---|
| EXIF strip detection | Photos downloaded from the web | `app/agents/photo_forensics.py` |
| Qwen-VL authenticity prompt | Watermarks ("alamy"), screenshots, AI-generation tells | `app/agents/photo_forensics.py` |
| Perceptual hash (pHash) | Near-identical re-uploads, stock-image matches | `app/clients/perceptual_hash.py` |
| Past-claim cosine similarity | Same-farmer narrative reuse | `app/agents/fraud_check.py` |
| Identity verification (KYC + liveness) | Claimant identity | `app/clients/identity_verification.py` |
| GPS distance vs claimed location | Impossible-travel detection | TODO |
| Velocity (claims/hr per phone) | Bot-like patterns | TODO |
| Device fingerprint + IP reputation | Suspicious origins | TODO |

No single layer is trusted. The dashboard surfaces all signals as flags
for the human adjuster.

---

## Privacy + data handling

- **Photos**: Encrypted at rest in OSS, signed-URL access only. Retention: 7 years (insurance regulatory default).
- **Identity documents**: Separate OSS prefix with stricter ACL, signed-URL TTL of 5 minutes. Retention: 5 years after account closure.
- **Vectors**: Stored in DashVector. No raw text; we embed claim narratives, not user identifiers.
- **Audit log**: Contains user IDs + action codes + counts, no PII bodies. Retention: 3 years.
- **Right to erasure** (GDPR Art. 17 / DPDP / LGPD / CCPA): Deletion endpoint TODO; the data model is shaped to make a single SQLite + OSS + DashVector cleanup possible.

---

## Open items (honest list)

- [ ] Non-root user inside the production Docker image
- [ ] CSP tightening (we currently allow `unsafe-inline` for shadcn at build time; move to nonces in production)
- [ ] Argon2id password hashing (currently PBKDF2)
- [ ] Real CSRF tokens for non-JSON form posts (today we rely on `SameSite=Lax`)
- [ ] Distributed rate limiting (in-process limiter won't survive horizontal scaling)
- [ ] Real signed URLs everywhere photos appear in the dashboard (some still pass through raw HTTP)
- [ ] Account deletion + GDPR-style data export endpoint
- [ ] Pen test by a third party
- [ ] Dependency scanning (Dependabot / npm audit / `pip-audit`)
- [ ] WAF in front of FC (Cloudflare or Alibaba WAF)

This list is the to-do queue; don't read "open" as "broken" — these
are the items past hackathon scope.
