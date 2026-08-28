"""Public feed WebSocket (killed by Anti-Panic)."""

from __future__ import annotations

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.identity.services import Actor
from apps.moderation.blocks import blocked_author_keys_for
from apps.stories.realtime import FEED_GROUP


class FeedConsumer(AsyncJsonWebsocketConsumer):
    """
    Protocol (JSON):
      client → { "type": "ping" }
      server → { "type": "pong" }
      server → { "type": "story.published"|"story.updated"|"story.hidden"|"story.unhidden", "story": {...} }
      server → { "type": "story.deleted", "story_id": "...", "author_key": "..." }
    """

    actor: Actor
    blocked: set[str]

    async def connect(self):
        self.actor = self.scope.get("actor") or Actor(kind="anonymous", session=None)
        self.blocked = await self._blocked_keys()
        await self.channel_layer.group_add(FEED_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(FEED_GROUP, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if (content or {}).get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def story_event(self, event):
        event_type = event.get("event_type") or ""
        payload = dict(event.get("payload") or {})
        key = payload.get("author_key")
        if not key and isinstance(payload.get("story"), dict):
            key = payload["story"].get("author_key")
        if key and key in self.blocked:
            return
        if event_type == "story.deleted":
            await self.send_json(
                {
                    "type": "story.deleted",
                    "story_id": payload.get("story_id"),
                    "author_key": payload.get("author_key"),
                }
            )
            return
        if event_type == "story.commented":
            post_id = payload.pop("post_id", None) or payload.get("parent_id")
            await self.send_json(
                {"type": "story.commented", "story": payload, "post_id": post_id}
            )
            return
        await self.send_json({"type": event_type, "story": payload})

    @database_sync_to_async
    def _blocked_keys(self) -> set[str]:
        return blocked_author_keys_for(self.actor)
