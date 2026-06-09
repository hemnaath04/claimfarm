"""Stand-in insurer REST API. Built out in Task #9."""

from fastapi import FastAPI

app = FastAPI(title="Mock Insurer", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
