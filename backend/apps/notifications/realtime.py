"""Broadcast notification events to per-recipient Channel layer groups."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.identity.services import Actor
from apps.notifications.models import Notification


def notif_group_for(actor: Actor) -> str | None:
    """Per-recipient group key. Anonymous sessions are addressed by session id."""
    if actor.account is not None:
        return f"notify.account.{actor.account.id}"
    if actor.session is not None:
        return f"notify.session.{actor.session.id}"
    return None


def serialize_notification(notif: Notification) -> dict[str, Any]:
    return {
        "id": str(notif.id),
        "kind": notif.kind,
        "payload": notif.payload or {},
        "is_read": bool(notif.is_read),
        "created_at": notif.created_at.isoformat(),
    }


def broadcast_notification(notif: Notification, recipient: Actor) -> None:
    """Send a live nudge to the recipient's notification group (if connected)."""
    group = notif_group_for(recipient)
    if group is None:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    payload = serialize_notification(notif)
    async_to_sync(layer.group_send)(
        group,
        {"type": "notification.new", "payload": payload},
    )