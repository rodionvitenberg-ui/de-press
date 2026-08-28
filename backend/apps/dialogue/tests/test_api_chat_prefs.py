from __future__ import annotations

import json

import pytest
from django.test import Client

from apps.dialogue.services import accept_request, create_request, send_message
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.stories.services import publish_story


@pytest.mark.django_db
def test_chat_prefs_http_contract():
    acc = Account.objects.create_user(email="api-prefs@ex.com", password="password123")
    author = Actor(kind="account", account=acc)
    story = publish_story(author, "prefs story")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    d = accept_request(author, create_request(peer, story.id, intent="listen").id)
    send_message(peer, d.id, "hi")

    client = Client()
    client.force_login(acc)
    did = d.id

    pin = client.post(f"/api/v1/dialogues/{did}/pin-chat")
    assert pin.status_code == 200
    assert pin.json()["pinned"] is True

    mute = client.post(f"/api/v1/dialogues/{did}/mute")
    assert mute.status_code == 200
    assert mute.json()["muted"] is True

    unread = client.post(f"/api/v1/dialogues/{did}/mark-unread")
    assert unread.status_code == 200
    assert unread.json()["unread_count"] >= 1

    listed = client.get("/api/v1/me/dialogues")
    assert listed.status_code == 200
    row = next(x for x in listed.json() if x["id"] == str(did))
    assert row["pinned"] is True
    assert row["muted"] is True
    assert row["unread_count"] >= 1

    read = client.post(f"/api/v1/dialogues/{did}/mark-read")
    assert read.status_code == 200
    assert read.json()["unread_count"] == 0

    clear = client.post(
        f"/api/v1/dialogues/{did}/clear-history",
        data=json.dumps({"scope": "me"}),
        content_type="application/json",
    )
    assert clear.status_code == 200
    msgs = client.get(f"/api/v1/dialogues/{did}/messages")
    assert msgs.status_code == 200
    assert msgs.json() == []


@pytest.mark.django_db
def test_get_one_dialogue():
    acc = Account.objects.create_user(email="api-one@ex.com", password="password123")
    author = Actor(kind="account", account=acc)
    story = publish_story(author, "one story")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    d = accept_request(author, create_request(peer, story.id, intent="listen").id)
    client = Client()
    client.force_login(acc)
    res = client.get(f"/api/v1/dialogues/{d.id}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == str(d.id)
    assert body["intent"] == "listen"
    assert "peer_label" in body
    assert body["peer_key"].startswith("s:")
