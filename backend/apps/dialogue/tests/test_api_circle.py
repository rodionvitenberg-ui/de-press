from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.dialogue.services import accept_request
from apps.dialogue.tests.helpers import create_reviewed_request
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.stories.services import publish_story


@pytest.mark.django_db
def test_post_circle_endpoint(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    acc = Account.objects.create_user(email="api-c@ex.com", password="password123")
    author = Actor(kind="account", account=acc)
    story = publish_story(author, "api circle")
    peer = Actor(kind="anonymous", session=AnonymousSession.objects.create())
    d = accept_request(
        author, create_reviewed_request(peer, story, intent="listen").id
    )
    client = Client()
    client.force_login(acc)
    res = client.post(
        f"/api/v1/dialogues/{d.id}/messages/circle",
        data={
            "video": SimpleUploadedFile("c.webm", b"abcd", content_type="video/webm"),
            "duration_ms": "1500",
            "source_lang": "ru",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["kind"] == "circle"
    assert body["ephemeral"] is True
    assert body["video_url"]
