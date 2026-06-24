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

- **Function Compute URL**: _added after deploy_
- **OSS bucket**: `claimfarm-files` (region `ap-southeast-1`)
- **DashVector collections**: `past_claims`, `agronomy_kb`
- **Console screenshots** (in `docs/screenshots/`):
  - `fc-function-overview.png` — FC dashboard
  - `oss-bucket.png` — OSS bucket with uploaded objects
  - `dashvector-collections.png` — DashVector with indexed claims
- **Live-call screen recording**: linked from the Devpost submission's
  "Proof of Alibaba Cloud Deployment" field.
