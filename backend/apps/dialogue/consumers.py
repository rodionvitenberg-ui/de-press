"""WebSocket consumer for Initiated Dialogue realtime."""

from __future__ import annotations

import asyncio
from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.dialogue import calls
from apps.dialogue.help import list_help_inbox
from apps.dialogue.models import Dialogue, DialogueStatus
from apps.dialogue.queue_realtime import HELPERS_GROUP, serialize_queue_request
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
      client → { "type": "call.ring" }
      client → { "type": "call.accept" | "call.decline" | "call.end" }
      client → { "type": "call.offer" | "call.answer", "sdp": "..." }
      client → { "type": "call.ice", "candidate": {...} }
      server → { "type": "message.new", "message": {...} }
      server → { "type": "dialogue.closed", "dialogue": {...} }
      server → { "type": "typing", "typing": bool, "from_me": bool, ... }
      server → { "type": "history", "messages": [...] }
      server → { "type": "error", "detail": "..." }
      server → { "type": "pong" }
      server → { "type": "call.outgoing" | "call.incoming" | "call.accepted",
                 "call_id": "..." }
      server → { "type": "call.offer" | "call.answer", "call_id", "sdp" }
      server → { "type": "call.ice", "call_id", "candidate": {...} }
      server → { "type": "call.ended", "call_id", "reason" }
      server → { "type": "call.busy" }
    """

    dialogue_id: str
    group_name: str
    actor: Actor
    _typing: bool
    _typing_events: list[float]

    # Max typing events per window (flood control)
    TYPING_WINDOW_SEC = 2.0
    TYPING_MAX_EVENTS = 6

    # Max ICE candidates relayed per window (flood control)
    ICE_WINDOW_SEC = 2.0
    ICE_MAX_EVENTS = 100

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

        self._ice_events: list[float] = []
        calls.register_channel(self.dialogue_id, self.channel_name)

        history = await self._history()
        await self.send_json(
            {
                "type": "history",
                "messages": history,
                "status": dialogue.status,
            }
        )

        # Reconnect while ringing: re-deliver the incoming call to the callee.
        redeliver = calls.rebind_channel(
            self.dialogue_id, self._call_actor_key(), self.channel_name
        )
        if redeliver == "incoming":
            st = calls.get(self.dialogue_id)
            if st is not None:
                await self.send_json(
                    {"type": "call.incoming", "call_id": st["call_id"]}
                )

    async def disconnect(self, code):
        if getattr(self, "_typing", False) and hasattr(self, "group_name"):
            await self._broadcast_typing(False)
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if hasattr(self, "dialogue_id"):
            calls.unregister_channel(self.dialogue_id, self.channel_name)
            st = calls.get(self.dialogue_id)
            if st is not None and self.channel_name in (
                st.get("caller_channel"),
                st.get("callee_channel"),
            ):
                calls.end(self.dialogue_id)
                await calls.notify_ended(self.dialogue_id, st, "connection")

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

        if msg_type == "call.ring":
            await self._call_ring()
            return

        if msg_type == "call.accept":
            await self._call_accept()
            return

        if msg_type == "call.decline":
            await self._call_decline()
            return

        if msg_type == "call.offer":
            await self._relay_call_sdp("call.offer", content.get("sdp"))
            return

        if msg_type == "call.answer":
            await self._relay_call_sdp("call.answer", content.get("sdp"))
            return

        if msg_type == "call.ice":
            await self._relay_call_ice(content.get("candidate"))
            return

        if msg_type == "call.end":
            st = calls.end(self.dialogue_id)
            await calls.notify_ended(self.dialogue_id, st, "hangup")
            return

        await self.send_json({"type": "error", "detail": "Unknown event type"})

    async def chat_message(self, event):
        payload = dict(event["payload"])
        payload["from_me"] = self._from_me(payload)
        await self.send_json({"type": "message.new", "message": payload})

    async def dialogue_closed(self, event):
        st = calls.get(self.dialogue_id) if hasattr(self, "dialogue_id") else None
        if st is not None:
            calls.end(self.dialogue_id)
            await calls.notify_ended(self.dialogue_id, st, "closed")
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

    # --- Live 1:1 voice (ADR 0021): unicast signaling relay -----------------

    def _call_actor_key(self) -> str:
        return calls.actor_key(
            str(self.actor.account.id) if self.actor.account else None,
            str(self.actor.session.id)
            if self.actor.session and not self.actor.account
            else None,
        )

    async def _call_ring(self) -> None:
        try:
            dialogue = await self._get_dialogue()
        except DialogueError:
            await self.send_json({"type": "error", "detail": "Dialogue not found"})
            return
        if dialogue.status != DialogueStatus.OPEN:
            await self.send_json(
                {"type": "error", "detail": "Dialogue is not open"}
            )
            return
        st = calls.start(
            self.dialogue_id, self._call_actor_key(), self.channel_name
        )
        if st is None:
            await self.send_json({"type": "call.busy"})
            return
        calls.set_ring_task(
            self.dialogue_id,
            asyncio.ensure_future(calls.ring_timeout(self.dialogue_id)),
        )
        await self.channel_layer.send(
            self.channel_name,
            {
                "type": "call.outgoing",
                "call_id": st["call_id"],
                "timeout": calls.RING_TIMEOUT_SEC,
            },
        )
        incoming = {"type": "call.incoming", "call_id": st["call_id"]}
        for ch in calls.channels_for(self.dialogue_id):
            if ch != self.channel_name:
                await self.channel_layer.send(ch, incoming)

    async def _call_accept(self) -> None:
        st = calls.get(self.dialogue_id)
        key = self._call_actor_key()
        if st is None or st["state"] != "ringing" or key == st["caller_key"]:
            await self.send_json({"type": "error", "detail": "No ringing call"})
            return
        if calls.find_for_actor(key) not in (None, self.dialogue_id):
            # Callee is already in another call: auto-decline this one.
            calls.end(self.dialogue_id)
            await calls.notify_ended(self.dialogue_id, st, "busy")
            return
        calls.attach_callee(self.dialogue_id, key, self.channel_name)
        msg = {"type": "call.accepted", "call_id": st["call_id"]}
        await self.channel_layer.send(st["caller_channel"], msg)
        await self.channel_layer.send(self.channel_name, msg)

    async def _call_decline(self) -> None:
        st = calls.get(self.dialogue_id)
        if st is None:
            return
        if self._call_actor_key() == st["caller_key"]:
            return
        calls.end(self.dialogue_id)
        await calls.notify_ended(self.dialogue_id, st, "declined")

    def _call_target(self, st: dict) -> str | None:
        """The other side of the active call for this connection."""
        if self._call_actor_key() == st["caller_key"]:
            return st.get("callee_channel")
        return st.get("caller_channel")

    async def _relay_call_sdp(self, event_type: str, sdp) -> None:
        sdp = calls.clean_sdp(sdp)
        if sdp is None:
            await self.send_json({"type": "error", "detail": "Bad SDP"})
            return
        st = calls.get(self.dialogue_id)
        if st is None or st["state"] != "active":
            return
        target = self._call_target(st)
        if target:
            await self.channel_layer.send(
                target, {"type": event_type, "call_id": st["call_id"], "sdp": sdp}
            )

    async def _relay_call_ice(self, candidate) -> None:
        if not self._allow_ice_event():
            return
        cand = calls.clean_candidate(candidate)
        if cand is None:
            return
        st = calls.get(self.dialogue_id)
        if st is None:
            return
        target = self._call_target(st)
        if target:
            await self.channel_layer.send(
                target,
                {"type": "call.ice", "call_id": st["call_id"], "candidate": cand},
            )

    def _allow_ice_event(self) -> bool:
        """Sliding-window throttle for ICE floods."""
        import time

        now = time.monotonic()
        window = self.ICE_WINDOW_SEC
        self._ice_events = [t for t in self._ice_events if now - t < window]
        if len(self._ice_events) >= self.ICE_MAX_EVENTS:
            return False
        self._ice_events.append(now)
        return True

    async def _passthrough_call(self, event: dict) -> None:
        # Layer event name == wire event name (call.outgoing, call.ice, ...)
        await self.send_json(event)

    async def call_outgoing(self, event):
        await self._passthrough_call(event)

    async def call_incoming(self, event):
        await self._passthrough_call(event)

    async def call_accepted(self, event):
        await self._passthrough_call(event)

    async def call_offer(self, event):
        await self._passthrough_call(event)

    async def call_answer(self, event):
        await self._passthrough_call(event)

    async def call_ice(self, event):
        await self._passthrough_call(event)

    async def call_ended(self, event):
        await self._passthrough_call(event)

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


class HelperQueueConsumer(AsyncJsonWebsocketConsumer):
    """
    Live human-help queue for the Helper dashboard (P5, Q4). Helpers only.

    Protocol (JSON):
      client → { "type": "ping" }
      client → { "type": "queue.refresh" }
      server → { "type": "snapshot", "queue": [...] }
      server → { "type": "queue.new", "request": {...} }
      server → { "type": "queue.taken", "id": "..." }
      server → { "type": "queue.cancelled", "id": "..." }
      server → { "type": "error", "detail": "..." }
      server → { "type": "pong" }
    """

    actor: Actor
    group_name: str | None

    async def connect(self):
        self.actor = self.scope.get("actor") or Actor(kind="anonymous", session=None)
        self.group_name = None

        account = self.actor.account
        if account is None or not account.is_helper:
            await self.close(code=4403)
            return

        self.group_name = HELPERS_GROUP
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._push_snapshot()

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = (content or {}).get("type")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})
            return
        if msg_type == "queue.refresh":
            await self._push_snapshot()
            return
        await self.send_json({"type": "error", "detail": "Unknown event type"})

    async def queue_new(self, event):
        await self.send_json({"type": "queue.new", "request": event["payload"]})

    async def queue_taken(self, event):
        await self.send_json({"type": "queue.taken", "id": event["payload"]["id"]})

    async def queue_cancelled(self, event):
        await self.send_json({"type": "queue.cancelled", "id": event["payload"]["id"]})

    async def _push_snapshot(self):
        queue = await self._snapshot_queue()
        await self.send_json({"type": "snapshot", "queue": queue})

    @database_sync_to_async
    def _snapshot_queue(self) -> list[dict]:
        # Same view as the HTTP inbox: skips and own requests excluded;
        # empty while off duty (duty gate lives in list_help_inbox).
        return [serialize_queue_request(req) for req in list_help_inbox(self.actor)]
