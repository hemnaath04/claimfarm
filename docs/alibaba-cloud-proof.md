# Proof of Alibaba Cloud Deployment

> This document satisfies the hackathon's hard requirement:
> _"You must demonstrate that the backend is running on Alibaba Cloud."_

## Code references

| Alibaba Cloud service | File | What it does |
|---|---|---|
| **Object Storage Service (OSS)** | [`app/clients/alibaba_oss.py`](../app/clients/alibaba_oss.py) | Stores farmer-submitted photos and generated claim PDFs |
| **DashVector** | [`app/clients/vector_store.py`](../app/clients/vector_store.py) (`DashVectorStore` class) | RAG: past-claim retrieval, agronomy KB, fraud-pattern similarity |
| **Function Compute 3.0** | [`Dockerfile`](../Dockerfile) + [`deploy/README.md`](../deploy/README.md) | Hosts the FastAPI orchestrator as a custom-container function |

All three are addressed via the `oss2`, `dashvector`, and standard HTTP
runtime, declared in [`pyproject.toml`](../pyproject.toml).

## Configuration

The runtime reads Alibaba credentials from environment variables defined in
[`app/config.py`](../app/config.py):

- `ALIBABA_ACCESS_KEY_ID`
- `ALIBABA_ACCESS_KEY_SECRET`
- `ALIBABA_REGION`
- `OSS_BUCKET`, `OSS_ENDPOINT`
- `DASHVECTOR_API_KEY`, `DASHVECTOR_ENDPOINT`
- `VECTOR_STORE=dashvector` (switches the abstract `VectorStore` to the
  Alibaba backend; default is local Chroma for dev)

## Deployment evidence

The live deployment is documented below.

- **Function Compute URL** (live): https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run
  - `GET /healthz` → `{"status":"ok"}` (HTTP 200)
  - `GET /docs` → Swagger UI for the FastAPI app
  - `GET /openapi.json` → machine-readable API spec
- **OSS bucket**: `claimfarm-files` (region `ap-southeast-1`); test object at
  `oss://claimfarm-files/tests/smoke.txt` is publicly readable.
- **DashVector cluster**: `claimfarm` at
  `vrs-sg-b0q4uc3th0001u.dashvector.ap-southeast-1.aliyuncs.com`, two
  collections live: `agronomy_kb` (15 docs, 1024-dim cosine) and
  `past_claims` (auto-indexed on every save).
- **Container Registry**: Alibaba Container Registry EE instance
  `claimfarm-acr` mirrors the same image at
  `claimfarm-acr-registry.ap-southeast-1.cr.aliyuncs.com/claimfarm-hb/claimfarm`.
  Image is also published to `ghcr.io/hemnaath04/claimfarm:latest` for
  FC's "Use Custom Repository Image" runtime path.
- **Live-call screen recording**: linked from the Devpost submission's
  "Proof of Alibaba Cloud Deployment" field.

Verification command:

```bash
curl -sS https://claimfarm-api-wovsxktpbk.ap-southeast-1.fcapp.run/healthz
# → {"status":"ok"}
```
