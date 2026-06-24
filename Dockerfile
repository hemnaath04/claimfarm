# syntax=docker/dockerfile:1.6
#
# Production image for the ClaimFarm FastAPI backend.
# Targets Alibaba Cloud Function Compute 3.0 custom-container runtime
# (any HTTP server that listens on $LISTEN_PORT works).

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    LISTEN_PORT=9000

# WeasyPrint native deps + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libharfbuzz0b \
        libcairo2 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-dejavu-core \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Use uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /usr/local/bin/

WORKDIR /app

# Cache deps layer
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy app code
COPY app app
COPY mock_insurer mock_insurer
COPY dashboard dashboard
COPY scripts scripts

# SQLite + Chroma can write to /tmp on Function Compute
ENV DATABASE_URL=sqlite:////tmp/claimfarm.sqlite \
    CHROMA_PATH=/tmp/.chroma \
    PUBLIC_BASE_URL=http://localhost:9000

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
    CMD curl -fsS http://localhost:${LISTEN_PORT}/healthz || exit 1

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${LISTEN_PORT}"]
