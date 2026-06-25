# ClaimFarm

> Crop-insurance claims for the next 500 million smallholder farmers. One WhatsApp / Telegram photo, one filed claim, in any language — built on Qwen Cloud + Alibaba Cloud.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built on Qwen Cloud](https://img.shields.io/badge/Qwen%20Cloud-VL%20%2B%20Max%20%2B%20Embeddings-orange)](https://www.qwencloud.com/)
[![Backend: Alibaba Cloud](https://img.shields.io/badge/Backend-Alibaba%20Cloud-blue)](https://www.alibabacloud.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org)

Submitted to the **Global AI Hackathon Series with Qwen Cloud** — Track 4: Autopilot Agent.

| | URL |
|---|---|
| **Marketing + adjuster console** | https://claimfarm-dashboard.vercel.app |
| **API + agent backend** | https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run |
| **Live Telegram bot** | https://t.me/claimfarm_demo_bot |
| **Docs** | [Architecture](docs/architecture.md) · [Deployment](docs/deployment.md) · [API](docs/api.md) · [Security](docs/security.md) · [Onboarding](docs/onboarding.md) |

## Why

~500 million smallholder farmers globally lose crops to weather and pests every year. Less than 20% of eligible farmers ever file an insurance claim, because the forms are in the wrong language, demand structured evidence they cannot easily produce, and assume domain literacy. ClaimFarm collapses that workflow to a single photo.

## What it does

1. Farmer sends a damaged-crop photo (and optionally a few words in any language) to a Telegram or WhatsApp number.
2. **Qwen-VL-Max** assesses the photo: crop type, damage cause, severity, affected area, visible indicators.
3. **Photo forensics** layer (EXIF + Qwen-VL authenticity prompt + perceptual hashing) flags downloaded stock images, screenshots, AI generations, watermarks.
4. **Open-Meteo** historical weather is cross-referenced against the farmer's GPS and the photo's capture date to corroborate the diagnosis.
5. **Qwen embeddings + Alibaba DashVector** retrieve similar past claims, relevant agronomy guides, and possible fraud patterns.
6. **Qwen-Max** drafts a pre-filled claim PDF (WeasyPrint).
7. The claim lands in an adjuster's Next.js console for human review and approval.
8. On approval the claim is submitted to a mock insurer API; the farmer is notified in their own language.

## What's built

The product surface is a real, sellable SaaS:

- **Marketing site** — `/`, `/pricing`, `/about`, `/faq`, `/blog`, `/contact`, `/farmer`, `/legal/terms`, `/legal/privacy`
- **Auth** — sign-up, sign-in, sign-out, password reset, email verification, server-side sessions, RBAC (`owner > admin > moderator > reviewer > farmer`), audit log
- **Identity verification** — provider abstraction (MockProvider by default; Stripe Identity, Persona, Veriff, Onfido subclasses ready)
- **Adjuster console** — `/admin`: queue, AI assessment, weather corroboration, photo forensics, similar past claims, fraud flags, localized farmer message, decision controls
- **User dashboard** — `/dashboard`: overview, billing (Stripe stub), team + RBAC, API & webhooks, notifications, settings
- **Channels** — Telegram (working end-to-end), Twilio + Bird WhatsApp (code shipped, trial-tier limits documented)
- **Payments** — Stripe Checkout + webhook abstraction (stub-mode when unset)
- **Notifications** — multi-channel dispatcher (email, SMS, in-app) with templates
- **DevOps** — Dockerfile, docker-compose.yml, GitHub Actions for backend lint+test and web typecheck+build, dual-push to Alibaba ACR + ghcr.io
- **Docs** — architecture, deployment, API reference, security + threat model, developer onboarding, demo video script

## Tech stack

| Layer | Choice |
|---|---|
| Language (backend) | Python 3.11 |
| Backend framework | FastAPI |
| Web (marketing + dashboard) | Next.js 16 (App Router, Turbopack) + Tailwind v4 + shadcn/ui |
| Auth | PBKDF2-SHA256 + opaque server-side sessions in SQLModel |
| Vision | Qwen-VL-Max |
| Reasoning | Qwen-Max |
| Embeddings | Qwen text-embedding-v3 (1024-dim) |
| Vector DB | Alibaba DashVector (primary), Chroma local for dev |
| Relational | SQLite (dev + FC) → Alibaba Tablestore (planned prod swap) |
| File storage | Alibaba OSS |
| Farmer channels | Telegram Bot API, Twilio Programmable Messaging, Bird Conversations |
| Weather | Open-Meteo historical archive |
| PDF | WeasyPrint |
| Identity verification | Provider abstraction (Stripe Identity / Persona / Veriff / Onfido) |
| Payments | Stripe (stub-mode without keys) |
| Deployment | Alibaba Function Compute 3.0 (backend) + Vercel (web) |

## Local setup

```bash
git clone https://github.com/hemnaath04/claimfarm.git
cd claimfarm
cp .env.example .env       # fill QWEN_API_KEY at minimum
uv sync

# Terminal 1: FastAPI
uv run uvicorn app.main:app --port 8000 --reload

# Terminal 2: Streamlit fallback (optional)
uv run streamlit run dashboard/main.py

# Terminal 3: Next.js dashboard
cd web && pnpm install && pnpm dev
```

Or with Docker Compose:

```bash
docker compose up --build
# api at http://localhost:8000  ·  web at http://localhost:3000
```

## Repo layout

```
claimfarm/
├── app/                        # FastAPI orchestrator
│   ├── agents/                 # damage_assessor, weather_corroborator,
│   │                           # photo_forensics, past_claim_rag, agronomy_rag,
│   │                           # fraud_check, multilingual, claim_drafter,
│   │                           # whatsapp_intake (channel-agnostic)
│   ├── auth/                   # passwords, sessions, one-time tokens, routes
│   ├── clients/                # qwen, weather, vector_store, embeddings,
│   │                           # alibaba_oss, insurer, twilio_client, bird_client,
│   │                           # telegram_client, identity_verification,
│   │                           # perceptual_hash, notifications, stripe_client
│   ├── models/                 # pydantic schemas (damage, weather, claim,
│   │                           # forensics, user)
│   ├── storage/                # SQLModel repos: claims, users, farmer_profiles,
│   │                           # audit_log
│   ├── api_admin.py            # admin API (user search/suspend/role/audit)
│   ├── api_billing.py          # Stripe checkout + webhook
│   ├── api_claims.py           # adjuster console API
│   ├── api_identity.py         # KYC session + result
│   ├── main.py                 # FastAPI app composition
│   └── middlewares.py          # rate limiting + security headers
├── mock_insurer/               # Stand-in insurer carrier (mounted at /insurer)
├── dashboard/                  # Streamlit fallback (mature, retained)
├── web/                        # Next.js 16 marketing + admin + dashboard
│   ├── src/app/                #   /, /pricing, /about, /faq, /blog, /contact,
│   │                           #   /farmer, /legal/*, /auth/*, /admin, /dashboard
│   ├── src/components/         # marketing + shadcn UI primitives
│   └── src/lib/api.ts          # typed client for the FastAPI JSON API
├── scripts/                    # seed_agronomy_kb, seed_demo_claim, reindex_claims,
│                               # test_damage, test_weather, test_claim_pdf,
│                               # test_rag, test_multilingual, test_forensics
├── deploy/                     # Function Compute config + env template
├── docs/                       # architecture, deployment, api, security,
│                               # onboarding, demo-video-script
├── data/                       # demo_seed.json (3 canned claims for FC cold start)
├── Dockerfile                  # python:3.11-slim + pango/cairo + uvicorn
├── docker-compose.yml          # full stack for local dev
└── .github/workflows/          # docker-build.yml (image), ci.yml (lint + test)
```

## Hackathon submission artifacts

- **Proof of Alibaba Cloud deployment**: [`docs/alibaba-cloud-proof.md`](docs/alibaba-cloud-proof.md)
- **Architecture diagram**: [`docs/architecture.md`](docs/architecture.md)
- **Demo video script**: [`docs/demo-video-script.md`](docs/demo-video-script.md)
- **Track**: 4 — Autopilot Agent

## License

[MIT](LICENSE)
