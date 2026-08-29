"""HTTP contract for stories feed and mutations."""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.identity.models import Account
from apps.identity.services import Actor
from apps.stories.services import hide_story, publish_story


@pytest.fixture
def account(db):
    return Account.objects.create_user(
        email="story-api@ex.com",
        password="password123",
        default_pseudonym="автор",
    )


@pytest.fixture
def client(account):
    c = Client()
    c.force_login(account)
    return c


@pytest.mark.django_db
def test_health_endpoint():
    res = Client().get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert "database" in body
    assert "channels" in body
    assert body["database"] is True


@pytest.mark.django_db
def test_topics_and_public_feed_include_author_key(account):
    publish_story(Actor(kind="account", account=account), "в ленте", topic="anxiety")
    anon = Client()
    topics = anon.get("/api/v1/topics")
    assert topics.status_code == 200
    assert any(t["value"] == "anxiety" for t in topics.json())

    feed = anon.get("/api/v1/stories")
    assert feed.status_code == 200
    items = feed.json()["items"]
    assert items
    assert items[0]["body"] == "в ленте"
    assert items[0]["author_key"] == f"a:{account.id}"
    assert "pulse_count" not in items[0]
    assert items[0]["cloud_unread"] == 0
    assert items[0]["my_phrase_key"] == ""
    assert items[0]["received_clouds"] == []


@pytest.mark.django_db
def test_publish_get_thread_edit_hide_unhide_delete(client, account):
    created = client.post(
        "/api/v1/stories",
        data={"body": "первая", "topic": "loneliness"},
        content_type="application/json",
    )
    assert created.status_code == 200
    story_id = created.json()["id"]
    assert created.json()["is_mine"] is True
    assert created.json()["author_key"] == f"a:{account.id}"

    got = client.get(f"/api/v1/stories/{story_id}")
    assert got.status_code == 200
    assert got.json()["body"] == "первая"

    thread = client.get(f"/api/v1/stories/{story_id}/thread")
    assert thread.status_code == 200
    assert len(thread.json()["items"]) == 1

    patched = client.patch(
        f"/api/v1/stories/{story_id}",
        data={"body": "вторая"},
        content_type="application/json",
    )
    assert patched.status_code == 200
    assert patched.json()["body"] == "вторая"

    hidden = client.post(f"/api/v1/stories/{story_id}/hide")
    assert hidden.status_code == 200
    assert hidden.json()["status"] == "hidden"
    assert Client().get(f"/api/v1/stories/{story_id}").status_code == 404

    shown = client.post(f"/api/v1/stories/{story_id}/unhide")
    assert shown.status_code == 200
    assert shown.json()["status"] == "published"

    mine = client.get("/api/v1/me/stories")
    assert mine.status_code == 200
    assert mine.json()[0]["id"] == story_id
    assert "author_key" in mine.json()[0]

    deleted = client.delete(f"/api/v1/stories/{story_id}")
    assert deleted.status_code == 200
    assert Client().get(f"/api/v1/stories/{story_id}").status_code == 404


@pytest.mark.django_db
def test_hidden_story_visible_only_to_author(account):
    actor = Actor(kind="account", account=account)
    story = publish_story(actor, "секрет")
    hide_story(actor, story.id)
    other = Account.objects.create_user(email="o@ex.com", password="password123")
    stranger = Client()
    stranger.force_login(other)
    assert stranger.get(f"/api/v1/stories/{story.id}").status_code == 404
    owner = Client()
    owner.force_login(account)
    assert owner.get(f"/api/v1/stories/{story.id}").status_code == 200


@pytest.mark.django_db
def test_publish_voice_http(client, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    settings.AI_API_KEY = ""
    audio = SimpleUploadedFile(
        "note.webm",
        b"\x1a\x45\xdf\xa3fake-webm-bytes",
        content_type="audio/webm",
    )
    res = client.post(
        "/api/v1/stories/voice",
        data={"audio": audio, "duration_ms": "1500", "topic": "anxiety"},
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["audio_url"]
    assert body["duration_ms"] == 1500
    # STT pipeline rolled back: offline voice publish has no transcript,
    # body is an optional caption and stays empty here.
    assert body["body"] == ""


@pytest.mark.django_db
def test_comment_http_author_only(client, account):
    created = client.post(
        "/api/v1/stories",
        data={"body": "пост"},
        content_type="application/json",
    )
    post_id = created.json()["id"]
    ok = client.post(
        f"/api/v1/stories/{post_id}/comments",
        data={"body": "мой коммент"},
        content_type="application/json",
    )
    assert ok.status_code == 200
    assert ok.json()["parent_id"] == post_id
    thread = client.get(f"/api/v1/stories/{post_id}/thread")
    assert [i["id"] for i in thread.json()["items"]] == [post_id, ok.json()["id"]]
    other = Account.objects.create_user(email="nope@ex.com", password="password123")
    stranger = Client()
    stranger.force_login(other)
    denied = stranger.post(
        f"/api/v1/stories/{post_id}/comments",
        data={"body": "чужой"},
        content_type="application/json",
    )
    assert denied.status_code == 403


@pytest.mark.django_db
def test_publish_rejects_empty_body(client):
    res = client.post(
        "/api/v1/stories",
        data={"body": "   "},
        content_type="application/json",
    )
    assert res.status_code == 400
