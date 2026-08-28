"""WebSocket consumer for Initiated Dialogue realtime."""

from __future__ import annotations

from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.dialogue.models import Dialogue
from apps.dialogue.realtime import dialogue_group, serialize_message
from apps.dialogue.services import (
    DialogueError,
    close_dialogue,
    get_dialogue_for_participant,
    list_messages,
    send_message,
)
from apps.identity.services import Actor


class DialogueConsumer(AsyncJsonWebsocketConsumer):
    """
    Protocol (JSON):
      client → { "type": "message.send", "body": "..." }
      client → { "type": "dialogue.close" }
      client → { "type": "typing.start" | "typing.stop" }
      client → { "type": "ping" }
      server → { "type": "message.new", "message": {...} }
      server → { "type": "dialogue.closed", "dialogue": {...} }
      server → { "type": "typing", "typing": bool, "from_me": bool, ... }
      server → { "type": "history", "messages": [...] }
      server → { "type": "error", "detail": "..." }
      server → { "type": "pong" }
    """

    dialogue_id: str
    group_name: str
    actor: Actor
    _typing: bool
    _typing_events: list[float]

    # Max typing events per window (flood control)
    TYPING_WINDOW_SEC = 2.0
    TYPING_MAX_EVENTS = 6

    async def connect(self):
        self.dialogue_id = self.scope["url_route"]["kwargs"]["dialogue_id"]
        self.actor = self.scope.get("actor") or Actor(kind="anonymous", session=None)
        self._typing = False
        self._typing_events = []

        if self.actor.account is None and self.actor.session is None:
            await self.close(code=4401)
            return

        try:
            UUID(self.dialogue_id)
        except ValueError:
            await self.close(code=4400)
            return

        try:
            dialogue = await self._get_dialogue()
        except DialogueError:
            await self.close(code=4403)
            return

        self.group_name = dialogue_group(self.dialogue_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        history = await self._history()
        await self.send_json(
            {
                "type": "history",
                "messages": history,
                "status": dialogue.status,
            }
        )

    async def disconnect(self, code):
        if getattr(self, "_typing", False) and hasattr(self, "group_name"):
            await self._broadcast_typing(False)
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = (content or {}).get("type")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})
            return

        if msg_type == "typing.start":
            if not self._allow_typing_event():
                return
            if not self._typing:
                self._typing = True
                await self._broadcast_typing(True)
            return

        if msg_type == "typing.stop":
            if not self._allow_typing_event():
                return
            if self._typing:
                self._typing = False
                await self._broadcast_typing(False)
            return

        if msg_type == "message.send":
            body = (content.get("body") or "").strip()
            if self._typing:
                self._typing = False
                await self._broadcast_typing(False)
            try:
                await self._send(body)
            except DialogueError as exc:
                await self.send_json({"type": "error", "detail": str(exc)})
                return
            return

        if msg_type == "dialogue.close":
            if self._typing:
                self._typing = False
                await self._broadcast_typing(False)
            try:
                await self._close()
            except DialogueError as exc:
                await self.send_json({"type": "error", "detail": str(exc)})
                return
            return

        await self.send_json({"type": "error", "detail": "Unknown event type"})

    async def chat_message(self, event):
        payload = dict(event["payload"])
        payload["from_me"] = self._from_me(payload)
        await self.send_json({"type": "message.new", "message": payload})

    async def dialogue_closed(self, event):
        await self.send_json({"type": "dialogue.closed", "dialogue": event["payload"]})

    async def dialogue_reopened(self, event):
        await self.send_json({"type": "dialogue.reopened", "dialogue": event["payload"]})

    async def message_edited(self, event):
        payload = dict(event["payload"])
        payload["from_me"] = self._from_me(payload)
        await self.send_json({"type": "message.edited", "message": payload})

    async def message_deleted(self, event):
        payload = dict(event["payload"])
        payload["from_me"] = self._from_me(payload)
        await self.send_json({"type": "message.deleted", "message": payload})

    async def dialogue_pinned(self, event):
        await self.send_json({"type": "dialogue.pinned", "dialogue": event["payload"]})

    async def typing_event(self, event):
        payload = dict(event["payload"])
        payload["from_me"] = self._actor_is(
            payload.get("from_account_id"),
            payload.get("from_session_id"),
        )
        # Skip echo for own typing — UI already knows
        if payload["from_me"]:
            return
        await self.send_json(
            {
                "type": "typing",
                "typing": bool(payload.get("typing")),
                "from_me": False,
            }
        )

    def _allow_typing_event(self) -> bool:
        """Simple sliding-window throttle for typing floods."""
        import time

        now = time.monotonic()
        window = self.TYPING_WINDOW_SEC
        self._typing_events = [t for t in self._typing_events if now - t < window]
        if len(self._typing_events) >= self.TYPING_MAX_EVENTS:
            return False
        self._typing_events.append(now)
        return True

    async def _broadcast_typing(self, typing: bool) -> None:
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing.event",
                "payload": {
                    "typing": typing,
                    "from_account_id": (
                        str(self.actor.account.id) if self.actor.account else None
                    ),
                    "from_session_id": (
                        str(self.actor.session.id)
                        if self.actor.session and not self.actor.account
                        else None
                    ),
                },
            },
        )

    def _from_me(self, payload: dict) -> bool:
        return self._actor_is(
            payload.get("from_account_id"),
            payload.get("from_session_id"),
        )

    def _actor_is(self, account_id: str | None, session_id: str | None) -> bool:
        if self.actor.account and account_id == str(self.actor.account.id):
            return True
        if self.actor.session and session_id == str(self.actor.session.id):
            return True
        return False

    @database_sync_to_async
    def _get_dialogue(self) -> Dialogue:
        return get_dialogue_for_participant(self.actor, UUID(self.dialogue_id))

    @database_sync_to_async
    def _history(self) -> list[dict]:
        msgs = list_messages(self.actor, UUID(self.dialogue_id))
        return [serialize_message(m, viewer=self.actor) for m in msgs]

    @database_sync_to_async
    def _send(self, body: str) -> object:
        return send_message(self.actor, UUID(self.dialogue_id), body)

    @database_sync_to_async
    def _close(self) -> Dialogue:
        return close_dialogue(self.actor, UUID(self.dialogue_id))
