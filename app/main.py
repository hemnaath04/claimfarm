import hashlib
import hmac
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request, Response

from app import (
    api_admin,
    api_billing,
    api_claims,
    api_farmers,
    api_gdpr,
    api_identity,
    api_invites,
    api_keys_routes,
    api_magic_link,
    logging_setup,
)
from app.agents import whatsapp_intake
from app.auth.routes import router as auth_router
from app.config import get_settings
from app.middlewares import IPRateLimiter, SecurityHeaders
from app.models.claim import Claim
from app.observability import init_sentry
from app.storage import claims_repo
from mock_insurer.main import app as mock_insurer_app

logging_setup.configure(level=get_settings().log_level)
init_sentry()

logger = logging.getLogger(__name__)

DEMO_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_seed.json"


def _seed_demo_claims_if_empty() -> None:
    """Populate the ephemeral SQLite with a few canned claims on cold start.

    FC writes SQLite to /tmp which is wiped between container instances, so
    without this seed every fresh deploy shows an empty queue. Seeds are
    only inserted if no claims exist — local dev data is untouched.
    """
    try:
        existing = claims_repo.list_by_status()
        if existing:
            return
        if not DEMO_SEED_PATH.exists():
            logger.info("no demo seed file at %s; skipping", DEMO_SEED_PATH)
            return
        payload = json.loads(DEMO_SEED_PATH.read_text())
        for c in payload:
            claim = Claim.model_validate(c)
            claims_repo.save(claim)
        logger.info("seeded %d demo claims", len(payload))
    except Exception:  # noqa: BLE001
        logger.exception("demo seed failed (continuing anyway)")


app = FastAPI(title="ClaimFarm", version="0.1.0")


@app.on_event("startup")
def _on_startup() -> None:
    _seed_demo_claims_if_empty()

# Mount the mock InsurerCo as a sub-app under /insurer so adjusters can
# approve claims without a second uvicorn running. In production this
# would be replaced by INSURER_BASE_URL pointing at a real carrier.
app.mount("/insurer", mock_insurer_app)

# Adjuster JSON API consumed by the Next.js dashboard (web/).
api_claims.install_api(app)

# Auth + identity + billing + admin + GDPR + API-keys + magic-link sub-APIs.
app.include_router(auth_router)
app.include_router(api_magic_link.router)
app.include_router(api_identity.router)
app.include_router(api_billing.router)
app.include_router(api_admin.router)
app.include_router(api_gdpr.router)
app.include_router(api_keys_routes.router)
# Farmer profiles (admin-only read) + invite-only access management. Importing
# these routers also registers their SQLModel tables (farmer_profiles, invites)
# on the shared metadata so create_all builds them at startup.
app.include_router(api_farmers.router)
app.include_router(api_invites.router)

# Cross-cutting middleware (registration order matters — last wraps first).
app.add_middleware(SecurityHeaders)
app.add_middleware(IPRateLimiter, rate=get_settings().rate_limit_per_minute)

# Bird payload logs land in /tmp so we can inspect them after the first call
BIRD_LOG = Path("/tmp/claimfarm_bird_payloads.jsonl")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


def _verify_twilio_signature(
    request: Request,
    params: dict[str, str],
) -> bool:
    """Validate X-Twilio-Signature using HMAC-SHA1 over the request URL + params.

    Twilio signs every webhook with HMAC-SHA1(auth_token, url + sorted_params).
    When TWILIO_AUTH_TOKEN is unset (dev/test), validation is skipped so local
    testing without a real Twilio account still works.

    We receive the already-parsed form params so we don't need to re-read the
    consumed stream — FastAPI's Form() parser runs before this function.

    See: https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    settings = get_settings()
    auth_token = settings.twilio_auth_token
    if not auth_token:
        # SEC-008: Twilio is not a configured channel (this deployment uses
        # Telegram only). An unconfigured webhook must be CLOSED, not open —
        # rejecting prevents an unauthenticated public intake surface.
        logger.warning("SEC-008: TWILIO_AUTH_TOKEN not set; rejecting webhook")
        return False

    twilio_sig = request.headers.get("X-Twilio-Signature", "")
    if not twilio_sig:
        return False

    try:
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(auth_token)
        return validator.validate(str(request.url), params, twilio_sig)
    except Exception:
        logger.exception("twilio signature validation failed")
        return False


@app.post("/twilio/inbound")
def twilio_inbound(
    request: Request,
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

    SEC-001: Validates the X-Twilio-Signature HMAC before dispatching.
    The parsed form params are passed to the validator so we don't need
    to re-read the already-consumed request stream.
    """
    form_params: dict[str, str] = {"From": From, "Body": Body, "NumMedia": NumMedia}
    if MediaUrl0 is not None:
        form_params["MediaUrl0"] = MediaUrl0
    if MediaContentType0 is not None:
        form_params["MediaContentType0"] = MediaContentType0

    if not _verify_twilio_signature(request, form_params):
        # Return 403 without TwiML so spoofed Twilio retries don't get through.
        raise HTTPException(status_code=403, detail="invalid webhook signature")

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


def _verify_bird_signature(request: Request, raw_body: bytes) -> bool:
    """Validate X-Bird-Signature-256 HMAC-SHA256.

    Bird signs webhook payloads with HMAC-SHA256(bird_webhook_secret, body).
    When BIRD_WEBHOOK_SECRET is unset, validation is skipped (dev mode).
    """
    settings = get_settings()
    secret = settings.bird_webhook_secret
    if not secret:
        # SEC-008: Bird is not a configured channel (Telegram only). Reject
        # an unconfigured webhook rather than leave it open to unsigned posts.
        logger.warning("SEC-008: BIRD_WEBHOOK_SECRET not set; rejecting webhook")
        return False

    sig_header = request.headers.get("X-Bird-Signature-256", "")
    if not sig_header:
        return False

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    # Header may be prefixed "sha256=" depending on Bird's format.
    received = sig_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@app.post("/bird/inbound")
async def bird_inbound(request: Request, background: BackgroundTasks) -> dict:
    """Bird (MessageBird) WhatsApp webhook.

    Bird sends JSON (not form-encoded like Twilio). We log the raw
    payload to /tmp/claimfarm_bird_payloads.jsonl on every call so we
    can inspect the actual schema once the first message arrives, then
    dispatch the pipeline against the standard intake.

    SEC-003: Validates HMAC-SHA256 signature before processing.
    """
    raw_body = await request.body()
    if not _verify_bird_signature(request, raw_body):
        raise HTTPException(status_code=403, detail="invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

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


def _verify_telegram_secret(request: Request) -> bool:
    """Validate X-Telegram-Bot-Api-Secret-Token header.

    When setWebhook is called with a `secret_token`, Telegram sends it on
    every update as X-Telegram-Bot-Api-Secret-Token. If TELEGRAM_WEBHOOK_SECRET
    is unset, validation is skipped (dev mode without a registered webhook).

    See: https://core.telegram.org/bots/api#setwebhook
    """
    settings = get_settings()
    expected = settings.telegram_webhook_secret
    if not expected:
        logger.warning("SEC-002: TELEGRAM_WEBHOOK_SECRET not set; skipping header check")
        return True

    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(expected, received)


@app.post("/telegram/inbound")
async def telegram_inbound(request: Request) -> dict:
    """Telegram Bot webhook. JSON `Update` payload per Telegram Bot API.

    The pipeline runs **synchronously** (in a worker thread) before we ack.
    On Function Compute the instance is frozen the moment the HTTP response
    returns, so a fire-and-forget BackgroundTask would never execute — the
    claim would never be filed and the farmer would never get a reply. The
    full pipeline finishes well within Telegram's webhook timeout, so we do
    the work first, then 200.

    SEC-002: Validates X-Telegram-Bot-Api-Secret-Token before processing.
    """
    from starlette.concurrency import run_in_threadpool

    if not _verify_telegram_secret(request):
        # Return 403; Telegram won't retry on non-2xx which prevents replay.
        raise HTTPException(status_code=403, detail="invalid webhook secret")

    try:
        update = await request.json()
    except Exception:
        update = {}

    parsed = whatsapp_intake.parse_telegram_update(update)
    if parsed:
        try:
            if parsed.get("callback_data") is not None:
                # Inline-button tap (language choice / "email me the PDF").
                await run_in_threadpool(
                    whatsapp_intake.process_telegram_callback,
                    chat_id=parsed["chat_id"],
                    user_name=parsed.get("user_name", ""),
                    data=parsed.get("callback_data"),
                    callback_query_id=parsed.get("callback_query_id"),
                )
            else:
                await run_in_threadpool(
                    whatsapp_intake.process_inbound_telegram,
                    chat_id=parsed["chat_id"],
                    user_name=parsed.get("user_name", ""),
                    body=parsed.get("body", ""),
                    photo_file_id=parsed.get("photo_file_id"),
                    mime=parsed.get("mime"),
                    location=parsed.get("location"),
                    is_start=bool(parsed.get("is_start")),
                )
        except Exception:
            logger.exception("telegram pipeline failed")

    # Always 200 so Telegram doesn't retry/duplicate the update.
    return {"ok": True}
