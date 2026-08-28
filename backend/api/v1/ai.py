from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.ai.services import AIError, support_chat
from apps.identity.services import require_actor

router = Router(tags=["ai"])


class MessageIn(Schema):
    role: str
    content: str


class SupportIn(Schema):
    messages: list[MessageIn]
    surface: str = "companion"


class SupportOut(Schema):
    reply: str
    crisis: bool
    offline: bool
    labeled_ai: bool
    disclaimer: str


@router.post("/ai/support", response=SupportOut)
def ai_support(request, payload: SupportIn):
    actor = require_actor(request)
    try:
        result = support_chat(
            actor,
            messages=[{"role": m.role, "content": m.content} for m in payload.messages],
            surface=payload.surface,
        )
    except AIError as exc:
        raise HttpError(400, str(exc)) from exc

    return SupportOut(
        reply=result.reply,
        crisis=result.crisis,
        offline=result.offline,
        labeled_ai=result.labeled_ai,
        disclaimer=(
            "Это ИИ-помощник, не терапевт и не экстренная служба. "
            "При кризисе — 112 / 103 и режим Anti-Panic."
        ),
    )
