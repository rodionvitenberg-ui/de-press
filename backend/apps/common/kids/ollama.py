"""Single-flight completions for sim_kids via local Ollama."""

from __future__ import annotations

import threading

import httpx
from django.conf import settings

SYSTEM = (
    "Ты тихий посетитель de-press. Без советов, без токсичного позитива, "
    "без диагнозов. 1–2 коротких предложения по-русски."
)

_lock = threading.Lock()


def complete(prompt: str, *, timeout: float = 20.0) -> str:
    base = str(getattr(settings, "KIDS_BASE_URL", "") or "").rstrip("/")
    model = str(getattr(settings, "KIDS_MODEL", "") or "qwen2.5:0.5b")
    key = str(getattr(settings, "KIDS_API_KEY", "") or "not-needed")
    if not base:
        return ""
    headers = {"Authorization": f"Bearer {key}"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 80,
    }
    with _lock:
        try:
            resp = httpx.post(
                f"{base}/chat/completions",
                json=body,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (
                ((data.get("choices") or [{}])[0].get("message") or {}).get("content")
                or ""
            )
            return str(text).strip()
        except Exception:
            return ""
