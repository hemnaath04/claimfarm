"""Qwen Cloud client (DashScope-International, OpenAI-compatible)."""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from app.config import get_settings


@lru_cache
def get_client() -> OpenAI:
    s = get_settings()
    return OpenAI(api_key=s.qwen_api_key, base_url=s.qwen_base_url)


def encode_image(path: str | Path) -> str:
    """Encode a local image as a base64 data URL accepted by Qwen-VL."""
    p = Path(path)
    suffix = p.suffix.lower().lstrip(".") or "jpeg"
    if suffix == "jpg":
        suffix = "jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:image/{suffix};base64,{b64}"


def vision_chat(
    *,
    system: str,
    user_text: str,
    image: str,
    model: str | None = None,
    json_mode: bool = True,
    max_tokens: int = 700,
    temperature: float = 0.2,
) -> str:
    """Single-turn vision chat. `image` may be a data URL or a public https URL."""
    s = get_settings()
    client = get_client()
    resp = client.chat.completions.create(
        model=model or s.qwen_vl_model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image}},
                    {"type": "text", "text": user_text},
                ],
            },
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"} if json_mode else None,
    )
    return resp.choices[0].message.content or ""


def text_chat(
    *,
    system: str,
    user_text: str,
    model: str | None = None,
    json_mode: bool = False,
    max_tokens: int = 700,
    temperature: float = 0.3,
) -> str:
    s = get_settings()
    client = get_client()
    resp = client.chat.completions.create(
        model=model or s.qwen_chat_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"} if json_mode else None,
    )
    return resp.choices[0].message.content or ""
