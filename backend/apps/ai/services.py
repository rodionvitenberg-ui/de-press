"""Deep AI support module: small interface for soft companion replies."""

from __future__ import annotations

from dataclasses import dataclass

from apps.ai.crisis import CRISIS_REPLY_RU, looks_like_crisis
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
        raise RateLimitExceeded("Слишком много обращений к помощнику. Подожди немного.")
    cache.set(key, count + 1, timeout=AI_WINDOW_SECONDS)


def support_chat(
    actor: Actor,
    *,
    messages: list[dict[str, str]],
    surface: str = "companion",
) -> SupportReply:
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
        raise AIError("Нужно последнее сообщение от пользователя")

    last_user = cleaned[-1].content
    if looks_like_crisis(last_user):
        return SupportReply(reply=CRISIS_REPLY_RU, crisis=True, offline=False)

    system = SYSTEM_ANTI_PANIC if surface == "anti_panic" else SYSTEM_COMPANION
    gateway = get_gateway()
    offline = gateway.__class__.__name__ == "OfflineGateway"

    full = [ChatMessage(role="system", content=system), *cleaned]
    try:
        text = gateway.complete(full)
    except Exception as exc:  # noqa: BLE001 — surface as soft error
        raise AIError(f"Помощник временно недоступен: {exc}") from exc

    # Second-pass crisis on model output not needed; on input already handled
    return SupportReply(reply=text, crisis=False, offline=offline)
