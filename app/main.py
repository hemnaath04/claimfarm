import logging

from fastapi import BackgroundTasks, FastAPI, Form, Response

from app.agents import whatsapp_intake

logger = logging.getLogger(__name__)

app = FastAPI(title="ClaimFarm", version="0.1.0")


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
