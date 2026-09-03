"""AI provider adapters (OpenAI-compatible HTTP)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: str  # system | user | assistant
    content: str


class AIGateway(Protocol):
    is_offline: bool

    def complete(self, messages: list[ChatMessage]) -> str: ...

    def stream(self, messages: list[ChatMessage]) -> Iterator[str]: ...


class OfflineGateway:
    """Deterministic fallback when no API key — still useful for dev/tests."""

    is_offline = True

    def complete(self, messages: list[ChatMessage]) -> str:
        last_user = ""
        for m in reversed(messages):
            if m.role == "user":
                last_user = m.content
                break
        snippet = (last_user[:120] + "…") if len(last_user) > 120 else last_user
        return (
            "I am here in text. What you describe sounds heavy — and it is allowed "
            "to feel this way. Which part presses the most right now?"
            + (f' (about "{snippet}")' if snippet else "")
            + "\n\n[offline mode: no API key configured; template reply]"
        )

    def stream(self, messages: list[ChatMessage]) -> Iterator[str]:
        # Nothing to stream offline — deliver as a single piece.
        yield self.complete(messages)


class OpenAICompatibleGateway:
    is_offline = False

    def __init__(self, *, api_key: str, base_url: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def complete(self, messages: list[ChatMessage]) -> str:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=0.6,
            max_tokens=500,
        )
        choice = resp.choices[0].message.content
        return (choice or "").strip() or "…"

    def stream(self, messages: list[ChatMessage]) -> Iterator[str]:
        payload = [{"role": m.role, "content": m.content} for m in messages]
        chunks = self._client.chat.completions.create(
            model=self._model,
            messages=payload,
            temperature=0.6,
            max_tokens=500,
            stream=True,
        )
        for chunk in chunks:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


def get_gateway() -> AIGateway:
    key = getattr(settings, "AI_API_KEY", "") or ""
    if not key.strip():
        return OfflineGateway()
    return OpenAICompatibleGateway(
        api_key=key.strip(),
        base_url=settings.AI_BASE_URL,
        model=settings.AI_MODEL,
    )
