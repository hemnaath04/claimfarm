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

## Deploy

In the FC 3.0 console:

1. Create function → **Custom Container** runtime
2. Image: pick the ACR image you just pushed
3. Port: 9000
4. Memory: 1 GB, Timeout: 60 s
5. Environment variables: paste the env list above
6. Trigger: HTTP, anonymous, GET + POST methods
7. Hit **Test** with `GET /healthz` — should return `{"status":"ok"}`

Production URL becomes `https://<function-name>.<account-id>.<region>.fcapp.run/`.
