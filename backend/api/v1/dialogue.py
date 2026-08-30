from __future__ import annotations

from uuid import UUID

from ninja import File, Form, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile as NinjaUploadedFile

from apps.dialogue.models import DialogueIntent, DialogueStatus
from apps.dialogue.realtime import serialize_message
from apps.dialogue.services import (
    DialogueError,
    RULES_TEXT,
    accept_request,
    clear_history,
    close_dialogue,
    create_request,
    delete_dialogue_for_everyone,
    delete_dialogue_for_me,
    delete_message_for_everyone,
    dialogue_flags,
    edit_message,
    forward_message,
    get_dialogue_for_participant,
    hide_message_for_me,
    decline_request,
    dialogue_last_preview,
    dialogue_peer_label,
    list_inbox,
    list_messages,
    list_my_dialogues,
    mark_dialogue_read,
    mark_dialogue_unread,
    mute_dialogue,
    pin_chat,
    pin_message,
    _is_muted,
    _pinned_at,
    reopen_dialogue,
    send_message,
    send_circle_message,
    send_voice_message,
    start_author_outreach,
    translate_message,
    unmute_dialogue,
    unpin_chat,
    unpin_message,
    unread_count_for,
)
from apps.identity.models import Account
from apps.identity.services import require_actor
from apps.stories.realtime import identity_key
from apps.stories.services import StoryNotFound

router = Router(tags=["dialogue"])


class RequestIn(Schema):
    intent: str
    note: str = ""


class RequestOut(Schema):
    id: str
    story_id: str
    intent: str
    note: str
    status: str
    created_at: str
    from_key: str = ""


class DialogueOut(Schema):
    id: str
    story_id: str | None
    intent: str
    status: str
    source: str
    rules: str
    updated_at: str
    peer_label: str = ""
    last_preview: str = ""
    closed_by_me: bool = False
    can_reopen: bool = False
    peer_hidden: bool = False
    hidden_for_me: bool = False
    pinned_message_id: str | None = None
    pinned: bool = False
    muted: bool = False
    unread_count: int = 0
    peer_key: str = ""
    peer_tip_wallet: str = ""


class OutreachIn(Schema):
    mode: str  # one | many | random
    hearer_refs: list[str] = []
    intent: str = "listen"


class OutreachOut(Schema):
    ok: bool
    created_count: int
    reused_count: int
    dialogues: list[DialogueOut]
    message: str


class MessageIn(Schema):
    body: str
    source_lang: str = "ru"
    reply_to_id: str | None = None


class MessageEditIn(Schema):
    body: str


class ForwardIn(Schema):
    dialogue_id: str


class PinIn(Schema):
    message_id: str


class ClearHistoryIn(Schema):
    scope: str = "me"


class MessageOut(Schema):
    id: str
    kind: str = "text"
    body: str
    display_text: str = ""
    transcript: str = ""
    source_lang: str = "ru"
    translations: dict[str, str] = {}
    duration_ms: int | None = None
    audio_url: str | None = None
    video_url: str | None = None
    ephemeral: bool = False
    created_at: str
    from_me: bool
    is_system: bool
    deleted: bool = False
    edited_at: str | None = None
    forwarded: bool = False
    forwarded_preview: str = ""
    reply_to: dict | None = None
    pinned: bool = False


class TranslateIn(Schema):
    target_lang: str = "en"


class IntentOut(Schema):
    value: str
    label: str


def _req_out(req) -> RequestOut:
    return RequestOut(
        id=str(req.id),
        story_id=str(req.story_id),
        intent=req.intent,
        note=req.note,
        status=req.status,
        created_at=req.created_at.isoformat(),
        from_key=identity_key(
            account_id=req.from_account_id,
            session_id=req.from_session_id,
        ),
    )


def _dialogue_out(d, actor=None) -> DialogueOut:
    flags = dialogue_flags(d, actor) if actor is not None else {}
    return DialogueOut(
        id=str(d.id),
        story_id=str(d.story_id) if d.story_id else None,
        intent=d.intent,
        status=d.status,
        source=getattr(d, "source", "request") or "request",
        rules=RULES_TEXT,
        updated_at=d.updated_at.isoformat(),
        peer_label=dialogue_peer_label(d, actor) if actor is not None else "",
        last_preview=dialogue_last_preview(d),
        closed_by_me=bool(flags.get("closed_by_me")),
        can_reopen=bool(flags.get("can_reopen")),
        peer_hidden=bool(flags.get("peer_hidden")),
        hidden_for_me=bool(flags.get("hidden_for_me")),
        pinned_message_id=(
            str(d.pinned_message_id) if getattr(d, "pinned_message_id", None) else None
        ),
        pinned=bool(_pinned_at(d, actor)) if actor is not None else False,
        muted=bool(_is_muted(d, actor)) if actor is not None else False,
        unread_count=unread_count_for(d, actor) if actor is not None else 0,
        peer_key=_peer_key(d, actor),
        peer_tip_wallet=_peer_tip_wallet(d, actor),
    )


def _peer_tip_wallet(d, actor) -> str:
    """Opt-in Solana tip address of a helper peer, only after dialogue closed.

    Shown only to the grateful side (the viewer is not the helper), only for
    a closed dialogue, and only when the helper opted in. Never on open
    dialogues, never on public pages (ADR-0020).
    """
    if actor is None or d.status != DialogueStatus.CLOSED:
        return ""
    is_author = False
    if actor.account is not None and d.author_account_id == actor.account.id:
        is_author = True
    if actor.session is not None and d.author_session_id == actor.session.id:
        is_author = True
    peer_account_id = d.peer_account_id if is_author else d.author_account_id
    if peer_account_id is None:
        return ""
    return (
        Account.objects.filter(id=peer_account_id, is_helper=True)
        .exclude(tip_wallet_address="")
        .values_list("tip_wallet_address", flat=True)
        .first()
    ) or ""


def _peer_key(d, actor) -> str:
    if actor is None:
        return ""
    i_am_author = False
    if actor.account and d.author_account_id == actor.account.id:
        i_am_author = True
    if actor.session and d.author_session_id == actor.session.id:
        i_am_author = True
    if i_am_author:
        return identity_key(
            account_id=d.peer_account_id,
            session_id=d.peer_session_id if d.peer_account_id is None else None,
        )
    return identity_key(
        account_id=d.author_account_id,
        session_id=d.author_session_id if d.author_account_id is None else None,
    )


def _message_out(m, *, actor) -> MessageOut:
    data = serialize_message(m, viewer=actor)
    return MessageOut(
        id=data["id"],
        kind=data.get("kind") or "text",
        body=data["body"],
        display_text=data.get("display_text") or data["body"],
        transcript=data.get("transcript") or "",
        source_lang=data.get("source_lang") or "ru",
        translations=data.get("translations") or {},
        duration_ms=data.get("duration_ms"),
        audio_url=data.get("audio_url"),
        video_url=data.get("video_url"),
        ephemeral=bool(data.get("ephemeral", False)),
        created_at=data["created_at"],
        from_me=data["from_me"],
        is_system=data["is_system"],
        deleted=bool(data.get("deleted")),
        edited_at=data.get("edited_at"),
        forwarded=bool(data.get("forwarded")),
        forwarded_preview=data.get("forwarded_preview") or "",
        reply_to=data.get("reply_to"),
        pinned=bool(data.get("pinned")),
    )


@router.get("/dialogue/intents", response=list[IntentOut])
def intents(request):
    return [IntentOut(value=v, label=str(label)) for v, label in DialogueIntent.choices]


@router.post("/stories/{story_id}/dialogue-requests", response=RequestOut)
def post_request(request, story_id: UUID, payload: RequestIn):
    actor = require_actor(request)
    try:
        req = create_request(
            actor,
            story_id,
            intent=payload.intent,
            note=payload.note,
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _req_out(req)


@router.get("/me/dialogue-requests", response=list[RequestOut])
def inbox(request):
    actor = require_actor(request)
    return [_req_out(r) for r in list_inbox(actor)]


@router.post("/dialogue-requests/{request_id}/accept", response=DialogueOut)
def accept(request, request_id: UUID):
    actor = require_actor(request)
    try:
        d = accept_request(actor, request_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/dialogue-requests/{request_id}/decline", response=RequestOut)
def decline(request, request_id: UUID):
    actor = require_actor(request)
    try:
        req = decline_request(actor, request_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _req_out(req)


@router.get("/me/dialogues", response=list[DialogueOut])
def my_dialogues(request):
    actor = require_actor(request)
    return [_dialogue_out(d, actor) for d in list_my_dialogues(actor)]


@router.get("/dialogues/{dialogue_id}", response=DialogueOut)
def get_dialogue(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        d = get_dialogue_for_participant(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.get("/dialogues/{dialogue_id}/messages", response=list[MessageOut])
def messages(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        msgs = list_messages(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return [_message_out(m, actor=actor) for m in msgs]


@router.post("/dialogues/{dialogue_id}/messages", response=MessageOut)
def post_message(request, dialogue_id: UUID, payload: MessageIn):
    actor = require_actor(request)
    try:
        m = send_message(
            actor,
            dialogue_id,
            payload.body,
            source_lang=payload.source_lang or "ru",
            reply_to_id=UUID(payload.reply_to_id) if payload.reply_to_id else None,
        )
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.post("/dialogues/{dialogue_id}/messages/voice", response=MessageOut)
def post_voice_message(
    request,
    dialogue_id: UUID,
    audio: NinjaUploadedFile = File(...),
    duration_ms: int | None = Form(None),
    source_lang: str = Form("ru"),
):
    actor = require_actor(request)
    try:
        m = send_voice_message(
            actor,
            dialogue_id,
            uploaded_file=audio,
            duration_ms=duration_ms,
            source_lang=source_lang or "ru",
        )
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.post("/dialogues/{dialogue_id}/messages/circle", response=MessageOut)
def post_circle_message(
    request,
    dialogue_id: UUID,
    video: NinjaUploadedFile = File(...),
    duration_ms: int | None = Form(None),
    source_lang: str = Form("ru"),
):
    actor = require_actor(request)
    try:
        m = send_circle_message(
            actor,
            dialogue_id,
            uploaded_file=video,
            duration_ms=duration_ms,
            source_lang=source_lang or "ru",
        )
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.patch("/messages/{message_id}", response=MessageOut)
def patch_message(request, message_id: UUID, payload: MessageEditIn):
    actor = require_actor(request)
    try:
        m = edit_message(actor, message_id, payload.body)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.delete("/messages/{message_id}", response=MessageOut)
def delete_message(request, message_id: UUID, scope: str = "me"):
    actor = require_actor(request)
    try:
        if scope == "everyone":
            m = delete_message_for_everyone(actor, message_id)
            return _message_out(m, actor=actor)
        hide_message_for_me(actor, message_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return MessageOut(
        id=str(message_id),
        kind="text",
        body="",
        display_text="",
        deleted=True,
        created_at="",
        from_me=True,
        is_system=False,
    )


@router.post("/messages/{message_id}/forward", response=MessageOut)
def post_forward(request, message_id: UUID, payload: ForwardIn):
    actor = require_actor(request)
    try:
        m = forward_message(actor, message_id, UUID(payload.dialogue_id))
    except (DialogueError, ValueError) as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.post("/dialogues/{dialogue_id}/pin", response=DialogueOut)
def post_pin(request, dialogue_id: UUID, payload: PinIn):
    actor = require_actor(request)
    try:
        d = pin_message(actor, UUID(payload.message_id))
        if d.id != dialogue_id:
            raise DialogueError("Сообщение из другого диалога")
    except (DialogueError, ValueError) as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/dialogues/{dialogue_id}/unpin", response=DialogueOut)
def post_unpin(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        d = unpin_message(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


def _dialogue_action(request, dialogue_id: UUID, fn):
    actor = require_actor(request)
    try:
        d = fn(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/dialogues/{dialogue_id}/pin-chat", response=DialogueOut)
def post_pin_chat(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, pin_chat)


@router.post("/dialogues/{dialogue_id}/unpin-chat", response=DialogueOut)
def post_unpin_chat(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, unpin_chat)


@router.post("/dialogues/{dialogue_id}/mute", response=DialogueOut)
def post_mute(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, mute_dialogue)


@router.post("/dialogues/{dialogue_id}/unmute", response=DialogueOut)
def post_unmute(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, unmute_dialogue)


@router.post("/dialogues/{dialogue_id}/mark-read", response=DialogueOut)
def post_mark_read(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, mark_dialogue_read)


@router.post("/dialogues/{dialogue_id}/mark-unread", response=DialogueOut)
def post_mark_unread(request, dialogue_id: UUID):
    return _dialogue_action(request, dialogue_id, mark_dialogue_unread)


@router.post("/dialogues/{dialogue_id}/clear-history", response=DialogueOut)
def post_clear_history(request, dialogue_id: UUID, payload: ClearHistoryIn):
    actor = require_actor(request)
    try:
        d = clear_history(actor, dialogue_id, scope=payload.scope or "me")
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/messages/{message_id}/translate", response=MessageOut)
def post_translate(request, message_id: UUID, payload: TranslateIn):
    actor = require_actor(request)
    try:
        m = translate_message(actor, message_id, target_lang=payload.target_lang)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _message_out(m, actor=actor)


@router.post("/dialogues/{dialogue_id}/close", response=DialogueOut)
def close(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        d = close_dialogue(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/dialogues/{dialogue_id}/reopen", response=DialogueOut)
def reopen(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        d = reopen_dialogue(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.delete("/dialogues/{dialogue_id}", response=DialogueOut)
def delete_mine(request, dialogue_id: UUID, scope: str = "me"):
    actor = require_actor(request)
    try:
        if scope == "everyone":
            d = delete_dialogue_for_everyone(actor, dialogue_id)
        else:
            d = delete_dialogue_for_me(actor, dialogue_id)
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc
    return _dialogue_out(d, actor)


@router.post("/stories/{story_id}/outreach", response=OutreachOut)
def post_outreach(request, story_id: UUID, payload: OutreachIn):
    actor = require_actor(request)
    try:
        result = start_author_outreach(
            actor,
            story_id,
            mode=payload.mode,  # type: ignore[arg-type]
            hearer_refs=payload.hearer_refs,
            intent=payload.intent or "listen",
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except DialogueError as exc:
        raise HttpError(400, str(exc)) from exc

    n = len(result.dialogues)
    if result.created_count and not result.reused_count:
        msg = f"Открыто диалогов: {result.created_count}."
    elif result.reused_count and not result.created_count:
        msg = "Диалог уже был открыт — продолжай переписку."
    else:
        msg = (
            f"Готово: новых {result.created_count}, "
            f"уже открытых {result.reused_count} (всего {n})."
        )
    return OutreachOut(
        ok=True,
        created_count=result.created_count,
        reused_count=result.reused_count,
        dialogues=[_dialogue_out(d, actor) for d in result.dialogues],
        message=msg,
    )
