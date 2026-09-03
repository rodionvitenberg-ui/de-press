"""Deep AI support module: small interface for soft companion replies."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from apps.ai.crisis import CRISIS_REPLY, looks_like_crisis
from apps.ai.gateway import ChatMessage, get_gateway
from apps.ai.prompts import SYSTEM_ANTI_PANIC, SYSTEM_COMPANION
from apps.common.rate_limit import RateLimitExceeded
from apps.identity.services import Actor

# Soft limit per hour
AI_LIMIT = 30
AI_WINDOW_SECONDS = 3600

ALLOWED_SURFACES = frozenset({"companion", "anti_panic"})
MAX_HISTORY = 12
MAX_MSG_LEN = 2000


class AIError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SupportReply:
    reply: str
    crisis: bool
    offline: bool
    labeled_ai: bool = True


@dataclass(frozen=True, slots=True)
class SupportStream:
    """Delta stream after eager validation (see stream_support_chat)."""

    chunks: Iterator[str]
    crisis: bool
    offline: bool


# In-memory rate counter store via Report-like: use a simple model-free approach
# counting is harder without a table — use django cache
def _rate_limit_ai(actor: Actor) -> None:
    from django.core.cache import cache

    if actor.account:
        key = f"ai_rl:acc:{actor.account.id}"
    elif actor.session:
        key = f"ai_rl:sess:{actor.session.id}"
    else:
        raise AIError("No identity")

    count = cache.get(key, 0)
    if count >= AI_LIMIT:
        raise RateLimitExceeded("Too many requests to the companion. Please wait a bit.")
    cache.set(key, count + 1, timeout=AI_WINDOW_SECONDS)


def _prepare(
    actor: Actor,
    *,
    messages: list[dict[str, str]],
    surface: str,
) -> list[ChatMessage]:
    """Shared validation for both reply paths: surface, identity, rate, history."""
    if surface not in ALLOWED_SURFACES:
        raise AIError("Invalid surface")
    if actor.account is None and actor.session is None:
        raise AIError("No identity")

    try:
        _rate_limit_ai(actor)
    except RateLimitExceeded as exc:
        raise AIError(str(exc)) from exc

    cleaned: list[ChatMessage] = []
    for raw in messages[-MAX_HISTORY:]:
        role = (raw.get("role") or "").strip()
        content = (raw.get("content") or "").strip()
        if role not in ("user", "assistant"):
            continue
        if not content:
            continue
        cleaned.append(ChatMessage(role=role, content=content[:MAX_MSG_LEN]))

    if not cleaned or cleaned[-1].role != "user":
        raise AIError("The last message must be from the user")
    return cleaned


def support_chat(
    actor: Actor,
    *,
    messages: list[dict[str, str]],
    surface: str = "companion",
) -> SupportReply:
    cleaned = _prepare(actor, messages=messages, surface=surface)

    last_user = cleaned[-1].content
    if looks_like_crisis(last_user):
        return SupportReply(reply=CRISIS_REPLY, crisis=True, offline=False)

    system = SYSTEM_ANTI_PANIC if surface == "anti_panic" else SYSTEM_COMPANION
    gateway = get_gateway()
    offline = gateway.is_offline

    full = [ChatMessage(role="system", content=system), *cleaned]
    try:
        text = gateway.complete(full)
    except Exception as exc:  # noqa: BLE001 — surface as soft error
        raise AIError(f"Companion is temporarily unavailable: {exc}") from exc

    # Second-pass crisis on model output not needed; on input already handled
    return SupportReply(reply=text, crisis=False, offline=offline)


def stream_support_chat(
    actor: Actor,
    *,
    messages: list[dict[str, str]],
    surface: str = "companion",
) -> SupportStream:
    """Same pipeline as support_chat, but yields deltas.

    Validation and the crisis short-circuit happen eagerly at call time, so
    the API layer can still answer 4xx before the SSE stream opens. Crisis
    replies come as one piece — no typewriter over the 112 instructions.
    """
    cleaned = _prepare(actor, messages=messages, surface=surface)

    last_user = cleaned[-1].content
    if looks_like_crisis(last_user):
        return SupportStream(chunks=iter([CRISIS_REPLY]), crisis=True, offline=False)

    system = SYSTEM_ANTI_PANIC if surface == "anti_panic" else SYSTEM_COMPANION
    gateway = get_gateway()
    offline = gateway.is_offline
    full = [ChatMessage(role="system", content=system), *cleaned]

    def _chunks() -> Iterator[str]:
        try:
            for delta in gateway.stream(full):
                if delta:
                    yield delta
        except AIError:
            raise
        except Exception as exc:  # noqa: BLE001 — surface as soft error
            raise AIError(f"Companion is temporarily unavailable: {exc}") from exc

    return SupportStream(chunks=_chunks(), crisis=False, offline=offline)
