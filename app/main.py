import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, Request, Response

from app.agents import whatsapp_intake

logger = logging.getLogger(__name__)

app = FastAPI(title="ClaimFarm", version="0.1.0")

# Bird payload logs land in /tmp so we can inspect them after the first call
BIRD_LOG = Path("/tmp/claimfarm_bird_payloads.jsonl")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/twilio/inbound")
def twilio_inbound(
    background: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str | None = Form(None),
    MediaContentType0: str | None = Form(None),
) -> Response:
    """Twilio WhatsApp webhook.

    Returns a TwiML acknowledgement immediately so Twilio's 15s timeout
    doesn't fire, then runs the full ClaimFarm pipeline in a background
    task. The pipeline ends with an outbound Twilio API call carrying
    the localized claim status back to the farmer.
    """
    background.add_task(
        whatsapp_intake.process_inbound,
        from_phone=From,
        body=Body,
        media_url=MediaUrl0,
        media_content_type=MediaContentType0,
    )

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Message>Got your photo. Hold on while we assess the damage — "
        "we'll reply in about a minute.</Message>"
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")


@app.post("/bird/inbound")
async def bird_inbound(request: Request, background: BackgroundTasks) -> dict:
    """Bird (MessageBird) WhatsApp webhook.

    Bird sends JSON (not form-encoded like Twilio). We log the raw
    payload to /tmp/claimfarm_bird_payloads.jsonl on every call so we
    can inspect the actual schema once the first message arrives, then
    dispatch the pipeline against the standard intake.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    try:
        BIRD_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BIRD_LOG.open("a") as fh:
            fh.write(
                json.dumps({"at": datetime.utcnow().isoformat(), "payload": payload})
                + "\n"
            )
    except Exception:
        logger.exception("could not write bird payload log")

    parsed = whatsapp_intake.parse_bird_payload(payload)
    if parsed:
        background.add_task(
            whatsapp_intake.process_inbound_bird,
            from_phone=parsed["from"],
            body=parsed.get("body", ""),
            media_url=parsed.get("media_url"),
            media_content_type=parsed.get("media_content_type"),
        )

    return {"status": "received"}


@app.post("/telegram/inbound")
async def telegram_inbound(request: Request, background: BackgroundTasks) -> dict:
    """Telegram Bot webhook. JSON `Update` payload per Telegram Bot API.

    Reliably works on the free tier — no media-access gymnastics,
    no template requirements, no 24-hour window.
    """
    try:
        update = await request.json()
    except Exception:
        update = {}

    parsed = whatsapp_intake.parse_telegram_update(update)
    if parsed:
        background.add_task(
            whatsapp_intake.process_inbound_telegram,
            chat_id=parsed["chat_id"],
            user_name=parsed.get("user_name", ""),
            body=parsed.get("body", ""),
            photo_file_id=parsed.get("photo_file_id"),
            mime=parsed.get("mime"),
        )

    # Telegram only cares about a 200 ack
    return {"ok": True}
