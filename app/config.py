import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Under pytest (conftest sets CLAIMFARM_TEST=1) do NOT read the developer's
# `.env` — otherwise a real RESEND_API_KEY in `.env` leaks into the suite and
# fires live emails (a test that delenv's the var re-exposes the file value).
# Tests configure everything they need via env vars + defaults.
_ENV_FILE = None if os.getenv("CLAIMFARM_TEST") else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    qwen_vl_model: str = "qwen-vl-max"
    qwen_chat_model: str = "qwen-max"
    qwen_embed_model: str = "text-embedding-v3"

    alibaba_access_key_id: str = ""
    alibaba_access_key_secret: str = ""
    alibaba_region: str = "ap-southeast-1"

    oss_bucket: str = "claimfarm-files"
    oss_endpoint: str = "https://oss-ap-southeast-1.aliyuncs.com"

    vector_store: str = "chroma"  # "chroma" or "dashvector"
    chroma_path: str = "./.chroma"

    dashvector_api_key: str = ""
    dashvector_endpoint: str = ""
    dashvector_cluster: str = ""

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    bird_api_key: str = ""
    bird_workspace_id: str = ""
    bird_channel_id: str = ""
    bird_sandbox_from: str = ""
    bird_base_url: str = "https://api.bird.com"
    # HMAC-SHA256 secret set in the Bird webhook configuration panel.
    # When set, every inbound Bird webhook is verified against the
    # X-Bird-Signature-256 header before the payload is processed.
    bird_webhook_secret: str = ""

    telegram_bot_token: str = ""
    telegram_api_base: str = "https://api.telegram.org"
    # Telegram allows setting a secret token on the setWebhook call; the
    # X-Telegram-Bot-Api-Secret-Token header on every update carries it.
    # Set this to any high-entropy string and pass it to setWebhook.
    telegram_webhook_secret: str = ""

    # Identity verification (KYC + liveness)
    identity_provider: str = "mock"  # mock | persona | veriff | onfido
    persona_api_key: str = ""
    veriff_api_key: str = ""
    onfido_api_key: str = ""

    # Payments — pick one (or leave 'none' to keep billing disabled).
    # Stripe is intentionally not bundled because account creation needs a US
    # SSN + registered business. Paddle and LemonSqueezy are merchant-of-record
    # alternatives that work for solo / international founders.
    payments_provider: str = "none"  # none | paddle | lemonsqueezy | razorpay
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_growth_price_id: str = ""
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_webhook_secret: str = ""
    lemonsqueezy_growth_variant_id: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Email / SMS / push transports (logged when unset)
    resend_api_key: str = ""
    resend_from: str = "ClaimFarm <onboarding@resend.dev>"
    sendgrid_api_key: str = ""
    twilio_sms_from: str = ""

    # SEC-007: secure-by-default. When True, the auth endpoints echo the
    # verification / reset / magic-link URLs (with live tokens) back in the
    # JSON response. That is convenient for local dev without SMTP, but in
    # production it is an account-takeover vector — POST /auth/reset with a
    # victim's registered email would return a working reset link. So this
    # defaults to FALSE; local dev opts in via AUTH_DEV_LINKS=true. In prod
    # configure RESEND_API_KEY for real email delivery instead.
    auth_dev_links: bool = False

    # Rate limiting
    rate_limit_per_minute: int = 60

    open_meteo_base: str = "https://archive-api.open-meteo.com/v1/archive"

    database_url: str = "sqlite:///./claimfarm.sqlite"
    public_base_url: str = "http://localhost:8000"
    # Web frontend root. Email-verify and magic-link consume redirect
    # here after the backend marks the token spent so the user lands on
    # the styled dashboard, not raw JSON.
    frontend_base_url: str = "http://localhost:3000"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
