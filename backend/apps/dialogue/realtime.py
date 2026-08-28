"""Broadcast dialogue events to Channel layer groups."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings

from apps.dialogue.models import Dialogue, Message
from apps.identity.services import Actor


def dialogue_group(dialogue_id: UUID | str) -> str:
    return f"dialogue.{dialogue_id}"


def audio_url_for(msg: Message) -> str | None:
    if not msg.audio:
        return None
    try:
        url = msg.audio.url
    except ValueError:
        return None
    # Absolute optional; clients prefix API origin if relative.
    media_base = getattr(settings, "MEDIA_URL", "/media/")
    if url.startswith("http"):
        return url
    if not url.startswith("/"):
        return f"{media_base.rstrip('/')}/{url.lstrip('/')}"
    return url


def video_url_for(msg: Message) -> str | None:
    if not getattr(msg, "video", None):
        return None
    try:
        url = msg.video.url
    except ValueError:
        return None
    media_base = getattr(settings, "MEDIA_URL", "/media/")
    if url.startswith("http"):
        return url
    if not url.startswith("/"):
        return f"{media_base.rstrip('/')}/{url.lstrip('/')}"
    return url


def serialize_message(msg: Message, *, viewer: Actor | None = None) -> dict[str, Any]:
    is_system = msg.from_account_id is None and msg.from_session_id is None
    from_me = False
    if viewer is not None:
        if viewer.account and msg.from_account_id == viewer.account.id:
            from_me = True
        if viewer.session and msg.from_session_id == viewer.session.id:
            from_me = True
    deleted = bool(getattr(msg, "deleted_at", None))
    reply = getattr(msg, "reply_to", None)
    reply_payload = None
    if reply is not None and not getattr(reply, "deleted_at", None):
        reply_payload = {
            "id": str(reply.id),
            "preview": (reply.display_text or "")[:140],
            "from_me": False,
        }
        if viewer is not None:
            if viewer.account and reply.from_account_id == viewer.account.id:
                reply_payload["from_me"] = True
            if viewer.session and reply.from_session_id == viewer.session.id:
                reply_payload["from_me"] = True
    pinned = False
    dialogue = getattr(msg, "dialogue", None)
    if dialogue is not None:
        pinned = getattr(dialogue, "pinned_message_id", None) == msg.id
    return {
        "id": str(msg.id),
        "kind": getattr(msg, "kind", "text") or "text",
        "body": "" if deleted else msg.body,
        "display_text": msg.display_text if hasattr(msg, "display_text") else msg.body,
        "transcript": "" if deleted else (getattr(msg, "transcript", "") or ""),
        "source_lang": getattr(msg, "source_lang", "") or "ru",
        "translations": {} if deleted else (getattr(msg, "translations", None) or {}),
        "duration_ms": None if deleted else getattr(msg, "duration_ms", None),
        "audio_url": None if deleted else audio_url_for(msg),
        "video_url": None if deleted else video_url_for(msg),
        "ephemeral": bool(getattr(msg, "ephemeral", False)),
        "created_at": msg.created_at.isoformat(),
        "from_me": from_me,
        "is_system": is_system,
        "from_account_id": str(msg.from_account_id) if msg.from_account_id else None,
        "from_session_id": str(msg.from_session_id) if msg.from_session_id else None,
        "deleted": deleted,
        "edited_at": msg.edited_at.isoformat() if getattr(msg, "edited_at", None) else None,
        "forwarded": bool(getattr(msg, "forwarded", False)),
        "forwarded_preview": getattr(msg, "forwarded_preview", "") or "",
        "reply_to": reply_payload,
        "pinned": pinned,
    }


def serialize_dialogue_closed(dialogue: Dialogue) -> dict[str, Any]:
    hidden_author = bool(getattr(dialogue, "hidden_for_author", False))
    hidden_peer = bool(getattr(dialogue, "hidden_for_peer", False))
    return {
        "id": str(dialogue.id),
        "status": dialogue.status,
        "closed_at": dialogue.closed_at.isoformat() if dialogue.closed_at else None,
        "abandoned": hidden_author or hidden_peer,
        "deleted_for_everyone": hidden_author and hidden_peer,
    }


def broadcast_chat_message(dialogue_id: UUID | str, message: Message) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    payload = serialize_message(message, viewer=None)
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue_id),
        {"type": "chat.message", "payload": payload},
    )


def broadcast_dialogue_closed(dialogue: Dialogue) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue.id),
        {"type": "dialogue.closed", "payload": serialize_dialogue_closed(dialogue)},
    )


def broadcast_message_edited(dialogue_id: UUID | str, message: Message) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue_id),
        {"type": "message.edited", "payload": serialize_message(message, viewer=None)},
    )


def broadcast_message_deleted(dialogue_id: UUID | str, message: Message) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue_id),
        {"type": "message.deleted", "payload": serialize_message(message, viewer=None)},
    )


def broadcast_dialogue_pinned(dialogue: Dialogue) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue.id),
        {
            "type": "dialogue.pinned",
            "payload": {
                "id": str(dialogue.id),
                "pinned_message_id": (
                    str(dialogue.pinned_message_id)
                    if dialogue.pinned_message_id
                    else None
                ),
            },
        },
    )


def broadcast_dialogue_reopened(dialogue: Dialogue) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        dialogue_group(dialogue.id),
        {
            "type": "dialogue.reopened",
            "payload": {
                "id": str(dialogue.id),
                "status": dialogue.status,
                "closed_at": None,
            },
        },
    )
