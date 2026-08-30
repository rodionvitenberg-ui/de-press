"""Translation adapter for dialogue messages and UI catalogs.

Deep interface: translate_text(text, target_lang).
Offline adapter for tests and no-key dev; online uses OpenAI-compatible APIs.
"""

from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

from apps.ai.gateway import ChatMessage, get_gateway

logger = logging.getLogger(__name__)


class Translator(Protocol):
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str: ...


def is_stub_translation(text: str) -> bool:
    t = (text or "").lstrip()
    return t.startswith("[offline") or t.startswith("[офлайн")


class OfflineTranslator:
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        t = (text or "").strip()
        if not t:
            return ""
        code = (target_lang or "en")[:2].lower()
        # Honest offline marker — not a fake translation. Stable ASCII sentinel
        # ("[offline {code}]") so clients detect it regardless of any locale.
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


def get_translator() -> Translator:
    return AITranslator()
