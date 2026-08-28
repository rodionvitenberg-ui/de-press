"""WebSocket consumer for per-recipient notifications (killed by Anti-Panic)."""

from __future__ import annotations

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.identity.services import Actor
from apps.notifications.realtime import notif_group_for, serialize_notification
from apps.notifications.services import (
    NotificationError,
    list_notifications,
    mark_read,
    mark_all_read,
    unread_count,
)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Protocol (JSON):
      client → { "type": "ping" }
      client → { "type": "notifications.read", "id": "..." }
      client → { "type": "notifications.read_all" }
      server → { "type": "snapshot", "notifications": [...], "unread_count": n }
      server → { "type": "notification.new", "notification": {...} }
      server → { "type": "notification.read", "id": "...", "is_read": true }
      server → { "type": "unread_count", "count": n }
      server → { "type": "pong" }
    """

    actor: Actor
    group_name: str | None

    async def connect(self):
        self.actor = self.scope.get("actor") or Actor(kind="anonymous", session=None)
        self.group_name = None

        if self.actor.account is None and self.actor.session is None:
            await self.close(code=4401)
            return

        group = notif_group_for(self.actor)
        if group is None:
            await self.close(code=4401)
            return

        self.group_name = group
        await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()

        notifs = await self._list()
        count = await self._unread_count()
        await self.send_json(
            {
                "type": "snapshot",
                "notifications": [serialize_notification(n) for n in notifs],
                "unread_count": count,
            }
        )

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = (content or {}).get("type")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})
            return

        if msg_type == "notifications.read":
            notif_id = (content.get("id") or "").strip()
            if not notif_id:
                await self.send_json({"type": "error", "detail": "Missing id"})
                return
            try:
                notif = await self._mark_read(notif_id)
            except NotificationError as exc:
                await self.send_json({"type": "error", "detail": str(exc)})
                return
            await self.send_json(
                {
                    "type": "notification.read",
                    "id": str(notif.id),
                    "is_read": True,
                }
            )
            count = await self._unread_count()
            await self.send_json({"type": "unread_count", "count": count})
            return

        if msg_type == "notifications.read_all":
            await self._mark_all_read()
            await self.send_json({"type": "unread_count", "count": 0})
            return

        await self.send_json({"type": "error", "detail": "Unknown event type"})

    async def notification_new(self, event):
        payload = dict(event["payload"])
        await self.send_json(
            {"type": "notification.new", "notification": payload}
        )
        count = await self._unread_count()
        await self.send_json({"type": "unread_count", "count": count})

    @database_sync_to_async
    def _list(self):
        return list_notifications(self.actor, limit=30)

    @database_sync_to_async
    def _unread_count(self):
        return unread_count(self.actor)

    @database_sync_to_async
    def _mark_read(self, notif_id: str):
        from uuid import UUID

        return mark_read(self.actor, UUID(notif_id))

    @database_sync_to_async
    def _mark_all_read(self):
        return mark_all_read(self.actor)