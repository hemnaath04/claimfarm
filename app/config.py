from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    telegram_bot_token: str = ""
    telegram_api_base: str = "https://api.telegram.org"

    # Identity verification (KYC + liveness)
    identity_provider: str = "mock"  # mock | stripe_identity | persona | veriff | onfido
    persona_api_key: str = ""
    veriff_api_key: str = ""
    onfido_api_key: str = ""

    # Stripe payments
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_growth_price_id: str = ""

    # Email / SMS / push transports (logged when unset)
    resend_api_key: str = ""
    sendgrid_api_key: str = ""
    twilio_sms_from: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 60

    open_meteo_base: str = "https://archive-api.open-meteo.com/v1/archive"

    database_url: str = "sqlite:///./claimfarm.sqlite"
    public_base_url: str = "http://localhost:8000"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
