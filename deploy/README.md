# Deploy → Alibaba Cloud Function Compute 3.0

This directory holds the deploy artifacts for the ClaimFarm backend.

## Architecture

```
GitHub Actions / Local push
       │
       ▼
Build Docker image (root Dockerfile)
       │
       ▼
Push to Alibaba Container Registry (ACR)
       │
       ▼
Function Compute 3.0 (custom container)
   │     │
   │     └── reads/writes Alibaba OSS (photos, PDFs)
   │
   └── reads/writes Alibaba DashVector (RAG)
```

## Configuration

The container listens on `${LISTEN_PORT}` (default 9000). FC routes HTTPS
to that port automatically. Required env vars (set in FC console):

- `QWEN_API_KEY` — Qwen Cloud key
- `ALIBABA_ACCESS_KEY_ID` / `ALIBABA_ACCESS_KEY_SECRET` — RAM user keys
- `OSS_BUCKET` / `OSS_ENDPOINT` — pick the same region as your FC function
- `DASHVECTOR_API_KEY` / `DASHVECTOR_ENDPOINT` — DashVector cluster
- `VECTOR_STORE=dashvector` — switch off local Chroma

## Build + push (CI)

Every push to `main` triggers `.github/workflows/docker-build.yml`, which builds
the image with Docker Buildx and pushes it to ACR EE at
`claimfarm-acr-registry.ap-southeast-1.cr.aliyuncs.com/claimfarm-hb/claimfarm`.

Required GitHub Actions secrets (Repo Settings → Secrets and variables → Actions):

- `ACR_USERNAME` — the Alibaba Cloud login email shown on the ACR EE
  Access Credential page (or a RAM user with `cr:Push` permission)
- `ACR_PASSWORD` — the password set on the same page

The workflow also accepts `workflow_dispatch`, so you can trigger a build
from the GitHub Actions tab without pushing.

## Build + push (manual fallback)

If you have Docker locally:

```bash
docker login --username=<email> claimfarm-acr-registry.ap-southeast-1.cr.aliyuncs.com
docker buildx build --platform linux/amd64 \
  -t claimfarm-acr-registry.ap-southeast-1.cr.aliyuncs.com/claimfarm-hb/claimfarm:latest \
  --push .
```

## Deploy (first time only)

In the FC 3.0 console:

1. Create function → **Custom Container** runtime
2. Image: a pinned digest tag, e.g. `ghcr.io/hemnaath04/claimfarm:<sha>`
   (never `:latest` — see note below)
3. Port: 9000
4. Memory: 1 GB, Timeout: 60 s
5. Environment variables: paste the env list above
6. Trigger: HTTP, anonymous, GET + POST methods
7. Hit **Test** with `GET /healthz` — should return `{"status":"ok"}`

Production URL becomes `https://<function-name>.<account-id>.<region>.fcapp.run/`.

## Auto-deploy on every push (no manual console step)

> Why this exists: `:latest` is a mutable tag — FC pins the *digest* at
> deploy time and never re-pulls, so pushing a new `:latest` either goes
> stale or "fails to be invoked". The CI step below updates FC to the new
> **immutable per-commit digest** automatically, so you never touch the
> console again.

After the image is pushed, `.github/workflows/docker-build.yml` runs
`deploy/fc_update_image.py`, which calls FC 3.0 `UpdateFunction` with **only**
`customContainerConfig.image` set — a partial update, so your environment
variables / port / timeout are preserved.

One-time setup (GitHub → repo **Settings → Secrets and variables → Actions**):

**Secrets:**
- `ALIBABA_FC_ACCESS_KEY_ID` — a RAM key with `fc:UpdateFunction`
  (the managed policy `AliyunFCFullAccess` is the easy choice)
- `ALIBABA_FC_ACCESS_KEY_SECRET`

**Variables:**
- `FC_ACCOUNT_ID` — your Alibaba Cloud account id (e.g. `5129681027390288`)
- `FC_REGION` — optional, defaults to `ap-southeast-1`
- `FC_FUNCTION_NAME` — optional, defaults to `claimfarm-api`

Until those secrets exist the deploy step **no-ops** (exit 0) so builds never
fail. Once set, every `git push` to `main` builds the image and rolls FC to
that exact commit — zero manual steps.
