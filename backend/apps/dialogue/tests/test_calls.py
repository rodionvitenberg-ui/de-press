"""Live 1:1 call signaling over the dialogue WS (ADR 0021)."""

from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore

from apps.dialogue import calls
from apps.dialogue.services import accept_request, close_dialogue
from apps.dialogue.tests.helpers import create_reviewed_request
from apps.identity.models import AnonymousSession
from apps.identity.services import Actor
from apps.stories.services import publish_story
from config.asgi import application

Account = get_user_model()


@pytest.fixture(autouse=True)
def _inmemory_layer(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }


async def _connect(url: str, headers: list[tuple[bytes, bytes]]):
    communicator = WebsocketCommunicator(application, url, headers=headers)
    connected, _ = await communicator.connect()
    assert connected is True
    first = await communicator.receive_json_from()
    assert first["type"] == "history"
    return communicator


@database_sync_to_async
def _session_key_for(author) -> str:
    store = SessionStore()
    store["_auth_user_id"] = str(author.id)
    store["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
    store["_auth_user_hash"] = author.get_session_auth_hash()
    store.save()
    return store.session_key


async def _connect_account(author, dialogue_id: str) -> WebsocketCommunicator:
    key = await _session_key_for(author)
    return await _connect(
        f"/ws/dialogues/{dialogue_id}/",
        [(b"cookie", f"sessionid={key}".encode())],
    )


async def _connect_anon(session, dialogue_id: str) -> WebsocketCommunicator:
    from django.conf import settings as dj_settings

    cookie = dj_settings.ANON_SESSION_COOKIE_NAME
    return await _connect(
        f"/ws/dialogues/{dialogue_id}/",
        [(b"cookie", f"{cookie}={session.id}".encode())],
    )


async def _pair():
    author = await database_sync_to_async(Account.objects.create_user)(
        email="calls-author@ex.com", password="password123"
    )
    author_actor = Actor(kind="account", account=author)
    story = await database_sync_to_async(publish_story)(
        author_actor, "call monologue", topic="anxiety"
    )
    peer_session = await database_sync_to_async(AnonymousSession.objects.create)(
        pseudonym="peer"
    )
    peer = Actor(kind="anonymous", session=peer_session)
    req = await database_sync_to_async(create_reviewed_request)(
        peer, story, intent="listen"
    )
    dialogue = await database_sync_to_async(accept_request)(author_actor, req.id)
    return {
        "author": author,
        "author_actor": author_actor,
        "peer_session": peer_session,
        "dialogue": dialogue,
    }


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_ring_accept_relay_hangup_flow():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    outgoing = await author_ws.receive_json_from()
    assert outgoing["type"] == "call.outgoing"
    call_id = outgoing["call_id"]

    incoming = await peer_ws.receive_json_from()
    assert incoming == {"type": "call.incoming", "call_id": call_id}

    await peer_ws.send_json_to({"type": "call.accept"})
    got_peer = await peer_ws.receive_json_from()
    got_author = await author_ws.receive_json_from()
    assert got_peer["type"] == got_author["type"] == "call.accepted"
    assert got_peer["call_id"] == got_author["call_id"] == call_id

    await author_ws.send_json_to({"type": "call.offer", "sdp": "v=0 offer"})
    offer = await peer_ws.receive_json_from()
    assert offer["type"] == "call.offer" and offer["sdp"] == "v=0 offer"
    assert offer["call_id"] == call_id

    await peer_ws.send_json_to({"type": "call.answer", "sdp": "v=0 answer"})
    answer = await author_ws.receive_json_from()
    assert answer["type"] == "call.answer" and answer["sdp"] == "v=0 answer"

    await peer_ws.send_json_to(
        {"type": "call.ice", "candidate": {"candidate": "candidate:1 udp"}}
    )
    ice = await author_ws.receive_json_from()
    assert ice["type"] == "call.ice"
    assert ice["candidate"]["candidate"] == "candidate:1 udp"

    await author_ws.send_json_to({"type": "call.end"})
    end_author = await author_ws.receive_json_from()
    end_peer = await peer_ws.receive_json_from()
    assert end_author["type"] == end_peer["type"] == "call.ended"
    assert end_author["reason"] == end_peer["reason"] == "hangup"
    assert end_author["call_id"] == call_id

    await author_ws.disconnect()
    await peer_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_decline_notifies_both_sides():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    assert (await author_ws.receive_json_from())["type"] == "call.outgoing"
    assert (await peer_ws.receive_json_from())["type"] == "call.incoming"

    await peer_ws.send_json_to({"type": "call.decline"})
    declined_author = await author_ws.receive_json_from()
    declined_peer = await peer_ws.receive_json_from()
    assert declined_author["reason"] == declined_peer["reason"] == "declined"

    await author_ws.disconnect()
    await peer_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_second_ring_is_busy():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    assert (await author_ws.receive_json_from())["type"] == "call.outgoing"
    assert (await peer_ws.receive_json_from())["type"] == "call.incoming"

    await peer_ws.send_json_to({"type": "call.ring"})
    assert (await peer_ws.receive_json_from()) == {"type": "call.busy"}

    await author_ws.disconnect()
    await peer_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_ring_closed_dialogue_rejected():
    pair = await _pair()
    await database_sync_to_async(close_dialogue)(
        Actor(kind="account", account=pair["author"]), pair["dialogue"].id
    )
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    err = await author_ws.receive_json_from()
    assert err["type"] == "error" and "not open" in err["detail"]

    await author_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_caller_disconnect_during_ring_notifies_callee():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    assert (await author_ws.receive_json_from())["type"] == "call.outgoing"
    assert (await peer_ws.receive_json_from())["type"] == "call.incoming"

    await author_ws.disconnect()
    ended = await peer_ws.receive_json_from()
    assert ended["type"] == "call.ended" and ended["reason"] == "connection"

    await peer_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_callee_disconnect_active_call_notifies_caller():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    assert (await author_ws.receive_json_from())["type"] == "call.outgoing"
    assert (await peer_ws.receive_json_from())["type"] == "call.incoming"
    await peer_ws.send_json_to({"type": "call.accept"})
    await peer_ws.receive_json_from()
    await author_ws.receive_json_from()

    await peer_ws.disconnect()
    ended = await author_ws.receive_json_from()
    assert ended["type"] == "call.ended" and ended["reason"] == "connection"

    await author_ws.disconnect()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reconnect_redelivers_incoming():
    pair = await _pair()
    author_ws = await _connect_account(pair["author"], str(pair["dialogue"].id))
    peer_ws = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))

    await author_ws.send_json_to({"type": "call.ring"})
    assert (await author_ws.receive_json_from())["type"] == "call.outgoing"
    assert (await peer_ws.receive_json_from())["type"] == "call.incoming"

    await peer_ws.disconnect()
    peer_ws2 = await _connect_anon(pair["peer_session"], str(pair["dialogue"].id))
    redelivered = await peer_ws2.receive_json_from()
    assert redelivered["type"] == "call.incoming"

    await author_ws.disconnect()
    await peer_ws2.disconnect()


@pytest.mark.django_db
def test_actor_busy_blocks_second_call():
    assert calls.start("d1", "account:1", "ch1") is not None
    assert calls.start("d2", "account:1", "ch2") is None
    assert calls.end("d1") is not None
    assert calls.start("d2", "account:1", "ch2") is not None
    calls.end("d2")


def test_sdp_and_candidate_cleaning():
    assert calls.clean_sdp("  v=0  ") == "v=0"
    assert calls.clean_sdp("") is None
    assert calls.clean_sdp(None) is None
    assert calls.clean_sdp("x" * (calls.MAX_SDP_LEN + 1)) is None
    assert calls.clean_candidate("candidate:1") == {"candidate": "candidate:1"}
    cand = {"candidate": "candidate:2", "sdpMid": "0", "sdpMLineIndex": 1, "junk": 1}
    assert calls.clean_candidate(cand) == {
        "candidate": "candidate:2",
        "sdpMid": "0",
        "sdpMLineIndex": 1,
    }
    assert calls.clean_candidate({"candidate": ""}) is None
    assert calls.clean_candidate(42) is None


@pytest.mark.django_db
def test_rtc_config_endpoint(settings):
    from django.test import Client

    settings.WEBRTC_TURN_URL = ""
    resp = Client().get("/api/v1/rtc/config")
    assert resp.status_code == 200
    assert resp.json()["ice_servers"] == []

    settings.WEBRTC_TURN_URL = "turn:coturn.example:3478?transport=udp"
    settings.WEBRTC_TURN_USERNAME = "u"
    settings.WEBRTC_TURN_CREDENTIAL = "p"
    data = Client().get("/api/v1/rtc/config").json()
    server = data["ice_servers"][0]
    assert "turn:coturn.example:3478?transport=udp" in server["urls"]
    assert "stun:coturn.example" in server["urls"]
    assert server["username"] == "u"
    assert server["credential"] == "p"

