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

## Build + push (manual)

```bash
# Login to ACR (replace region + namespace as configured in console)
docker login --username=<acr-user> registry.ap-southeast-1.aliyuncs.com

# Build for linux/amd64 (FC runs amd64)
docker buildx build --platform linux/amd64 \
  -t registry.ap-southeast-1.aliyuncs.com/<namespace>/claimfarm:latest \
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
