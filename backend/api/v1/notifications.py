from __future__ import annotations

from uuid import UUID

from ninja import Router, Schema

from apps.identity.services import require_actor
from apps.notifications.realtime import serialize_notification
from apps.notifications.services import (
    NotificationError,
    list_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)

router = Router(tags=["notifications"])


class NotificationOut(Schema):
    id: str
    kind: str
    payload: dict = {}
    is_read: bool = False
    created_at: str


class UnreadCountOut(Schema):
    count: int


class MarkReadOut(Schema):
    ok: bool
    id: str
    is_read: bool = True


class MarkAllReadOut(Schema):
    ok: bool
    updated: int


@router.get("/me/notifications", response=list[NotificationOut])
def list_my_notifications(request, limit: int = 30):
    actor = require_actor(request)
    rows = list_notifications(actor, limit=limit)
    return [serialize_notification(n) for n in rows]


@router.get("/me/notifications/unread-count", response=UnreadCountOut)
def my_unread_count(request):
    actor = require_actor(request)
    return UnreadCountOut(count=unread_count(actor))


@router.post("/me/notifications/{notification_id}/read", response=MarkReadOut)
def mark_one_read(request, notification_id: UUID):
    actor = require_actor(request)
    try:
        notif = mark_read(actor, notification_id)
    except NotificationError as exc:
        from ninja.errors import HttpError

        raise HttpError(400, str(exc)) from exc
    return MarkReadOut(ok=True, id=str(notif.id), is_read=notif.is_read)


@router.post("/me/notifications/read-all", response=MarkAllReadOut)
def mark_all_my_read(request):
    actor = require_actor(request)
    updated = mark_all_read(actor)
    return MarkAllReadOut(ok=True, updated=updated)