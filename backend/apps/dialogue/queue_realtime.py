"""Broadcast helper-queue events to the shared Helpers Channel group."""

from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

HELPERS_GROUP = "helpers.queue"


def serialize_queue_request(req) -> dict[str, Any]:
    """Queue row for Helpers. Only fields already visible via the inbox."""
    return {
        "id": str(req.id),
        "note": req.note or "",
        "created_at": req.created_at.isoformat(),
    }


def broadcast_queue_event(event_type: str, payload: dict[str, Any]) -> None:
    """Nudge every connected Helper (no-op when no channel layer / nobody there)."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        HELPERS_GROUP,
        {"type": event_type, "payload": payload},
    )
