from __future__ import annotations

import json

from django.http import StreamingHttpResponse
from ninja import Router, Schema
from ninja.errors import HttpError

from apps.ai.services import AIError, stream_support_chat, support_chat
from apps.identity.services import require_actor

router = Router(tags=["ai"])

AI_DISCLAIMER = (
    "Это ИИ-помощник, не терапевт и не экстренная служба. "
    "При кризисе — 112 / 103 и режим Anti-Panic."
)


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


def _sse_event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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
        disclaimer=AI_DISCLAIMER,
    )


@router.post("/ai/support/stream")
def ai_support_stream(request, payload: SupportIn):
    """SSE: event meta → delta* → done (or error mid-stream). Old POST stays."""
    actor = require_actor(request)
    try:
        stream = stream_support_chat(
            actor,
            messages=[{"role": m.role, "content": m.content} for m in payload.messages],
            surface=payload.surface,
        )
    except AIError as exc:
        raise HttpError(400, str(exc)) from exc

    def events():
        yield _sse_event(
            "meta",
            {"offline": stream.offline, "labeled_ai": True, "crisis": stream.crisis},
        )
        try:
            for chunk in stream.chunks:
                yield _sse_event("delta", {"text": chunk})
        except AIError as exc:
            yield _sse_event("error", {"detail": str(exc)})
            return
        yield _sse_event(
            "done",
            {"crisis": stream.crisis, "disclaimer": AI_DISCLAIMER},
        )

    response = StreamingHttpResponse(events(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
