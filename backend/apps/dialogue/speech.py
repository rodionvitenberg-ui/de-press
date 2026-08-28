"""STT and translation adapters for dialogue voice notes.

Deep interface: transcribe_audio(path) / translate_text(text, target_lang).
Offline adapters for tests and no-key dev; online uses OpenAI-compatible APIs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from django.conf import settings

from apps.ai.gateway import ChatMessage, get_gateway

logger = logging.getLogger(__name__)


class SpeechToText(Protocol):
    def transcribe(self, path: Path, *, language: str = "ru") -> str: ...


class Translator(Protocol):
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str: ...


class OfflineSTT:
    """Deterministic fallback when no STT key / provider."""

    def transcribe(self, path: Path, *, language: str = "ru") -> str:
        if language.startswith("en"):
            return "[offline transcript: voice note]"
        return "[офлайн-транскрипт: голосовое сообщение]"


class OpenAICompatibleSTT:
    """Whisper-style /audio/transcriptions on an OpenAI-compatible base URL."""

    def __init__(self, *, api_key: str, base_url: str, model: str):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def transcribe(self, path: Path, *, language: str = "ru") -> str:
        import httpx

        lang = language[:2] if language else "ru"
        url = f"{self._base_url}/audio/transcriptions"
        with path.open("rb") as fh:
            files = {"file": (path.name, fh, "application/octet-stream")}
            data = {"model": self._model, "language": lang}
            headers = {"Authorization": f"Bearer {self._api_key}"}
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, headers=headers, data=data, files=files)
                resp.raise_for_status()
                payload = resp.json()
        text = payload.get("text") if isinstance(payload, dict) else None
        return (text or "").strip() or OfflineSTT().transcribe(path, language=language)


def is_stub_translation(text: str) -> bool:
    t = (text or "").lstrip()
    return t.startswith("[offline") or t.startswith("[офлайн")


class OfflineTranslator:
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        t = (text or "").strip()
        if not t:
            return ""
        code = (target_lang or "en")[:2].lower()
        # Honest offline marker — not a fake translation.
        if code == "en":
            return f"[offline en] {t}"
        if code == "ru":
            return f"[офлайн ru] {t}"
        return f"[offline {code}] {t}"


class AITranslator:
    """Translate via dedicated OpenAI-compatible server, then the AI gateway."""

    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        t = (text or "").strip()
        if not t:
            return ""
        target = (target_lang or "en")[:2].lower()
        source = (source_lang or "").strip()[:2]
        dedicated = self._try_dedicated(t, target=target, source=source)
        if dedicated:
            return dedicated
        return self._via_gateway(t, target=target, source=source)

    def _messages(self, text: str, *, target: str, source: str) -> list[ChatMessage]:
        src_hint = f" from {source}" if source else ""
        system = (
            "You are a careful translator for a mental-health peer support chat. "
            "Translate the user message accurately. Preserve tone; do not add advice, "
            "diagnosis, or positivity. Output only the translation, no quotes or notes."
        )
        user = f"Translate{src_hint} to language code '{target}':\n\n{text}"
        return [
            ChatMessage(role="system", content=system),
            ChatMessage(role="user", content=user),
        ]

    def _try_dedicated(self, text: str, *, target: str, source: str) -> str | None:
        base = str(getattr(settings, "TRANSLATOR_BASE_URL", "") or "").strip()
        if not base:
            return None
        model = str(getattr(settings, "TRANSLATOR_MODEL", "") or "Hy-MT1.5-1.8B")
        key = str(getattr(settings, "TRANSLATOR_API_KEY", "") or "").strip() or "not-needed"
        payload = [
            {"role": m.role, "content": m.content}
            for m in self._messages(text, target=target, source=source)
        ]
        try:
            from openai import OpenAI

            client = OpenAI(api_key=key, base_url=base.rstrip("/"), timeout=30.0)
            resp = client.chat.completions.create(
                model=model,
                messages=payload,
                temperature=0,
                max_tokens=1024,
            )
            out = (resp.choices[0].message.content or "").strip()
            return out or None
        except Exception:
            logger.warning("dedicated translator failed; falling back", exc_info=False)
            return None

    def _via_gateway(self, text: str, *, target: str, source: str) -> str:
        gateway = get_gateway()
        from apps.ai.gateway import OfflineGateway

        if isinstance(gateway, OfflineGateway):
            return OfflineTranslator().translate(
                text, target_lang=target, source_lang=source
            )
        out = gateway.complete(self._messages(text, target=target, source=source))
        return (out or "").strip() or OfflineTranslator().translate(
            text, target_lang=target, source_lang=source
        )


def get_stt() -> SpeechToText:
    key = getattr(settings, "STT_API_KEY", "") or getattr(settings, "AI_API_KEY", "") or ""
    if not str(key).strip():
        return OfflineSTT()
    # Prefer dedicated STT base; fall back to OpenAI-ish default (not DeepSeek chat URL).
    base = getattr(settings, "STT_BASE_URL", "") or "https://api.openai.com/v1"
    model = getattr(settings, "STT_MODEL", "") or "whisper-1"
    return OpenAICompatibleSTT(
        api_key=str(key).strip(),
        base_url=str(base),
        model=str(model),
    )


def get_translator() -> Translator:
    return AITranslator()
