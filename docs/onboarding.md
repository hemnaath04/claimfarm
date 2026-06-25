# Developer onboarding

Welcome. This is the 30-minute path from cloning the repo to a green
local build + your first claim flowing through the pipeline.

---

## 1. Prerequisites

- Python 3.11
- Node 20
- [uv](https://github.com/astral-sh/uv) for Python deps (`brew install uv`)
- [pnpm](https://pnpm.io/) for JS deps (`corepack enable && corepack prepare pnpm@latest --activate`)
- Docker (optional, for the compose path)
- A Qwen Cloud API key (https://www.qwencloud.com/)

---

## 2. Clone + install

```bash
git clone https://github.com/hemnaath04/claimfarm.git
cd claimfarm
cp .env.example .env
# Open .env and paste QWEN_API_KEY at minimum. Everything else can stay empty —
# the system runs in mock-mode for any provider whose credential is unset.

uv sync                              # Python deps
cd web && pnpm install && cd ..      # Next.js deps
```

## 3. Run

Three terminals, three processes:

```bash
# Terminal 1 — FastAPI (the agent orchestrator + API)
uv run uvicorn app.main:app --port 8000 --reload

# Terminal 2 — Next.js (marketing + admin + dashboard)
cd web && pnpm dev

# Terminal 3 — Streamlit fallback adjuster console (optional)
uv run streamlit run dashboard/main.py
```

Open:
- http://localhost:3000  · marketing + Next.js admin
- http://localhost:8000/docs  · Swagger UI for the JSON API
- http://localhost:8501  · Streamlit adjuster fallback

## 4. Smoke-test the pipeline

```bash
# Run the damage assessor on a sample photo (Qwen-VL call)
uv run python scripts/test_damage.py data/eval/sample_drought_corn.jpg

# Full end-to-end: damage + weather + claim PDF
uv run python scripts/test_claim_pdf.py \
  data/eval/sample_drought_corn.jpg 35.15 -89.97 2007-08-15

# RAG layer (requires DASHVECTOR_* in .env OR VECTOR_STORE=chroma)
uv run python scripts/seed_agronomy_kb.py
uv run python scripts/test_rag.py

# Photo forensics (EXIF + Qwen-VL authenticity)
uv run python scripts/test_forensics.py data/eval/sample_drought_corn.jpg

# Multilingual reply layer
uv run python scripts/test_multilingual.py
```

## 5. Try the live Telegram bot

The hosted demo is at **t.me/claimfarm_demo_bot**. Send `/start`, share
your location, then a photo. Within ~30s you'll get back a reply in
the language of your caption.

To wire your own bot:
1. `/newbot` to BotFather → grab the token
2. Set `TELEGRAM_BOT_TOKEN` in `.env`
3. Register the webhook:
   ```bash
   uv run python -c "
   from dotenv import load_dotenv; load_dotenv()
   from app.clients import telegram_client
   print(telegram_client.set_webhook('https://your-host/telegram/inbound'))
   "
   ```

## 6. Try the auth + identity flow

```bash
TS=$(date +%s)
EMAIL="dev+${TS}@local.test"

# Sign up (first user becomes role=owner)
curl -sS -X POST http://localhost:8000/auth/sign-up \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"hunter22A!\",\"name\":\"Dev User\"}" \
  -c /tmp/cf

# Whoami
curl -sS http://localhost:8000/auth/me -b /tmp/cf

# Start an identity-verification session (MockProvider returns approved)
curl -sS -X POST http://localhost:8000/api/identity/start -b /tmp/cf

# Inspect the audit log (admin-only; first user is owner)
curl -sS "http://localhost:8000/api/admin/audit?limit=20" -b /tmp/cf
```

## 7. Where things live

| Need to … | Open |
|---|---|
| Tweak the damage prompt | `app/agents/damage_assessor.py` |
| Adjust weather corroboration | `app/agents/weather_corroborator.py` |
| Change the fraud thresholds | `app/agents/fraud_check.py` |
| Edit the PDF template | `app/templates/claim.html` |
| Add an auth route | `app/auth/routes.py` |
| Add an API route | `app/api_*.py` files; mount in `app/main.py` |
| Add an admin endpoint | `app/api_admin.py` |
| Customise the landing page | `web/src/app/page.tsx` |
| Customise the adjuster console | `web/src/app/admin/page.tsx` |
| Customise the dashboard tabs | `web/src/app/dashboard/page.tsx` |

## 8. Tests + CI

Local:

```bash
uv run python -m compileall -q app mock_insurer scripts
uv run ruff check app mock_insurer scripts
cd web && pnpm exec tsc --noEmit && pnpm build
```

CI: `.github/workflows/ci.yml` runs all of the above on every push to
`main`.

## 9. Deploying

See [`docs/deployment.md`](deployment.md). Backend deploys via
GitHub Actions → ACR/ghcr.io image → manual FC tag update. Web auto-deploys to Vercel on every push.

## 10. Where to ask for help

- Architecture questions → [`docs/architecture.md`](architecture.md)
- API questions → [`docs/api.md`](api.md) and `/docs` Swagger UI
- Security model → [`docs/security.md`](security.md)
- Demo recording → [`docs/demo-video-script.md`](demo-video-script.md)
