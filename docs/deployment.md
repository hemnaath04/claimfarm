# Deployment

End-to-end deployment guide for ClaimFarm. Two surfaces — the FastAPI
backend on Alibaba Function Compute 3.0, and the Next.js dashboard on
Vercel.

---

## 1. Backend (Alibaba Cloud)

### Prerequisites

- Alibaba Cloud account with payment + RAM user
- Activated services: OSS, DashVector, Function Compute, Container Registry
- A Qwen Cloud (DashScope-International) API key

### One-time setup

1. **OSS bucket** for photos + PDFs
   - Bucket name: `claimfarm-files` (any unique name)
   - Region: `ap-southeast-1` (Singapore) or match the rest of your stack
   - ACL: Private; objects served via signed URLs from `app/clients/alibaba_oss.py`

2. **RAM user** with `AliyunOSSFullAccess`
   - Save `ALIBABA_ACCESS_KEY_ID` and `ALIBABA_ACCESS_KEY_SECRET`

3. **DashVector cluster** with two collections
   - `past_claims` — 1024-dim, FLOAT, cosine
   - `agronomy_kb` — 1024-dim, FLOAT, cosine
   - Save `DASHVECTOR_API_KEY` and `DASHVECTOR_ENDPOINT`
   - Seed agronomy: `uv run python scripts/seed_agronomy_kb.py`

4. **Container Registry** (ACR EE Economy is sufficient for the FC pull
   path **only** if you also publish to `ghcr.io` — FC 3.0 cannot pull
   from ACR EE Economy directly. Publish to both registries via the
   `.github/workflows/docker-build.yml` workflow.)
   - GitHub Secrets needed: `ACR_USERNAME`, `ACR_PASSWORD`
   - First push to `main` builds + dual-publishes the image

5. **Function Compute 3.0 function** `claimfarm-api`
   - Runtime: **Custom Container** → **Use Custom Repository Image**
   - Image: `ghcr.io/<owner>/claimfarm:<sha>`
   - Port: 9000
   - Memory: 1024 MB · vCPU: 0.5 · Timeout: 120 s
   - Internet access: enabled
   - HTTP trigger: anonymous, all methods
   - Environment variables: see `deploy/fc-env-vars.txt`

### Subsequent deploys

```bash
git push origin main
# GitHub Actions auto-builds and dual-pushes to ACR + ghcr.io
# Then update the FC image tag (Configurations → Container Image)
#   ghcr.io/<owner>/claimfarm:<latest sha>
# Click Save — FC redeploys in ~20-30s
```

After redeploy:

```bash
curl https://<your-fn>-<account>.<region>.fcapp.run/healthz
# → {"status":"ok"}
```

---

## 2. Frontend (Vercel)

### Prerequisites

- Vercel account (free tier works)
- Project linked to the `web/` directory of the repo

### Deploy

```bash
cd web
vercel link                          # first time only
vercel env add NEXT_PUBLIC_API_URL production
# value: the FastAPI URL — either the live FC URL or a cloudflared tunnel
vercel deploy --prod --yes
```

Production URL (after the first deploy): `https://<project>.vercel.app`

`vercel.json` in `web/` locks the framework to Next.js and uses `pnpm`.

### Environment variables (Vercel)

| Key | Value | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<fc-url>` | The base URL the dashboard fetches against |

---

## 3. Telegram bot

```bash
# Create the bot with @BotFather, get the token, then:
TG_TOKEN="..." curl -sS -X POST \
  "https://api.telegram.org/bot$TG_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"https://<your-fn>.fcapp.run/telegram/inbound\", \"drop_pending_updates\": true}"
```

Set `TELEGRAM_BOT_TOKEN` in FC's env vars.

---

## 4. Twilio / Bird (WhatsApp)

Trial accounts on both providers have restrictions (cross-account media,
template-only outbound) — the integration code lives in
`app/clients/twilio_client.py` and `app/clients/bird_client.py` for when
those accounts are upgraded. Production deployments configure the
provider's "When a message comes in" webhook to point at
`https://<fc-url>/twilio/inbound` or `/bird/inbound`.

---

## 5. Identity verification

Default provider is `MockProvider` so the system runs end-to-end without
a real KYC vendor. To switch:

```bash
# Stripe Identity
IDENTITY_PROVIDER=stripe_identity
STRIPE_SECRET_KEY=sk_live_...
```

Wire other providers (Persona, Veriff, Onfido) by adding their subclass
to `app/clients/identity_verification.py`.

---

## 6. Stripe payments

Stripe is in stub mode until `STRIPE_SECRET_KEY` is set. Add it plus
`STRIPE_WEBHOOK_SECRET` and `STRIPE_GROWTH_PRICE_ID` to enable real
billing. Webhook endpoint: `https://<fc-url>/api/billing/webhook`.

---

## 7. Local development

```bash
cp .env.example .env       # fill QWEN_API_KEY at minimum
uv sync
uv run uvicorn app.main:app --port 8000 --reload &
uv run streamlit run dashboard/main.py &     # optional Streamlit fallback
cd web && pnpm install && pnpm dev &         # Next.js on :3000
```

Or with Docker Compose:

```bash
docker compose up --build
# api at http://localhost:8000
# web at http://localhost:3000
```
