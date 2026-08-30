"""Live 1:1 call signaling state (ADR 0021).

In-memory, per daphne process (single process per DEPLOY.md): a call dies
with its signaling process anyway, so no DB/Redis copy is kept. The server
only relays SDP/ICE between the two verified dialogue participants and
enforces one call per dialogue and per actor.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from channels.layers import get_channel_layer

RING_TIMEOUT_SEC = 45.0
MAX_SDP_LEN = 32_768
MAX_ICE_LEN = 2_048

# dialogue_id -> call state (see start())
_calls: dict[str, dict[str, Any]] = {}
# actor_key -> dialogue_id: one concurrent call per actor
_actor_calls: dict[str, str] = {}
# dialogue_id -> live signaling channels of its participants
_channels: dict[str, set[str]] = {}


def actor_key(account_id: str | None, session_id: str | None) -> str:
    if account_id:
        return f"account:{account_id}"
    if session_id:
        return f"session:{session_id}"
    return ""


def register_channel(dialogue_id: str, channel: str) -> None:
    _channels.setdefault(dialogue_id, set()).add(channel)


def unregister_channel(dialogue_id: str, channel: str) -> None:
    live = _channels.get(dialogue_id)
    if live is not None:
        live.discard(channel)
        if not live:
            _channels.pop(dialogue_id, None)


def channels_for(dialogue_id: str) -> list[str]:
    return list(_channels.get(dialogue_id, ()))


def get(dialogue_id: str) -> dict[str, Any] | None:
    return _calls.get(dialogue_id)


def find_for_actor(key: str) -> str | None:
    return _actor_calls.get(key)


def rebind_channel(dialogue_id: str, key: str, channel: str) -> str | None:
    """Reconnect while a call is ringing: point the participant's stored
    channel at the new socket. Returns "incoming" when this actor is the
    callee and must receive call.incoming again."""
    st = _calls.get(dialogue_id)
    if st is None:
        return None
    if key == st["caller_key"]:
        st["caller_channel"] = channel
        return None
    if st["state"] == "ringing" and st.get("callee_channel") is None:
        st["callee_channel"] = channel
        return "incoming"
    return None


def start(
    dialogue_id: str, caller_key: str, caller_channel: str
) -> dict[str, Any] | None:
    """Open a ringing call; None when the dialogue or the caller is busy."""
    if dialogue_id in _calls or (caller_key and caller_key in _actor_calls):
        return None
    st: dict[str, Any] = {
        "call_id": f"call-{uuid.uuid4().hex[:12]}",
        "caller_key": caller_key,
        "caller_channel": caller_channel,
        "callee_key": None,
        "callee_channel": None,
        "state": "ringing",
        "task": None,
    }
    _calls[dialogue_id] = st
    if caller_key:
        _actor_calls[caller_key] = dialogue_id
    return st


def set_ring_task(dialogue_id: str, task: asyncio.Task) -> None:
    st = _calls.get(dialogue_id)
    if st is not None:
        st["task"] = task


def attach_callee(
    dialogue_id: str, callee_key: str, callee_channel: str
) -> dict[str, Any] | None:
    st = _calls.get(dialogue_id)
    if st is None or st["state"] != "ringing":
        return None
    st["state"] = "active"
    st["callee_key"] = callee_key
    st["callee_channel"] = callee_channel
    _cancel_task(st)
    return st


def end(dialogue_id: str) -> dict[str, Any] | None:
    return _teardown(dialogue_id, _calls.get(dialogue_id))


def _teardown(dialogue_id: str, st: dict[str, Any] | None) -> dict[str, Any] | None:
    if st is None:
        return None
    _calls.pop(dialogue_id, None)
    for key in (st.get("caller_key"), st.get("callee_key")):
        if key and _actor_calls.get(key) == dialogue_id:
            _actor_calls.pop(key, None)
    _cancel_task(st)
    return st


def _cancel_task(st: dict[str, Any]) -> None:
    task = st.get("task")
    if task is not None and not task.done():
        task.cancel()
    st["task"] = None


async def notify_ended(
    dialogue_id: str, st: dict[str, Any] | None, reason: str
) -> None:
    """Unicast call.ended to the participants. While still ringing the
    callee channel is not attached yet — reach every live participant
    channel registered for the dialogue instead."""
    if not st:
        return
    layer = get_channel_layer()
    if layer is None:
        return
    msg = {"type": "call.ended", "call_id": st["call_id"], "reason": reason}
    targets = {
        ch
        for ch in (st.get("caller_channel"), st.get("callee_channel"))
        if ch
    }
    if st.get("state") == "ringing":
        targets |= set(_channels.get(dialogue_id, ())) - {st.get("caller_channel")}
    for ch in targets:
        await layer.send(ch, msg)


async def ring_timeout(dialogue_id: str) -> None:
    try:
        await asyncio.sleep(RING_TIMEOUT_SEC)
    except asyncio.CancelledError:
        return
    st = get(dialogue_id)
    if st is None or st["state"] != "ringing":
        return
    end(dialogue_id)
    await notify_ended(dialogue_id, st, "timeout")


def clean_sdp(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > MAX_SDP_LEN:
        return None
    return value


def clean_candidate(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        value = {"candidate": value}
    if not isinstance(value, dict):
        return None
    cand = value.get("candidate")
    if not isinstance(cand, str) or not cand or len(cand) > MAX_ICE_LEN:
        return None
    out: dict[str, Any] = {"candidate": cand}
    mid = value.get("sdpMid")
    if isinstance(mid, str) and len(mid) <= 64:
        out["sdpMid"] = mid
    idx = value.get("sdpMLineIndex")
    if isinstance(idx, int) and 0 <= idx <= 64:
        out["sdpMLineIndex"] = idx
    return out
