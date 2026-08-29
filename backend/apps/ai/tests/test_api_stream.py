from __future__ import annotations

import json

import pytest
from django.test import Client

from apps.identity.models import Account


def _post_stream(
    client: Client,
    messages: list[dict[str, str]],
    surface: str = "companion",
):
    return client.post(
        "/api/v1/ai/support/stream",
        data=json.dumps({"messages": messages, "surface": surface}),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_support_stream_sse_contract():
    acc = Account.objects.create_user(email="ai-stream@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    res = _post_stream(client, [{"role": "user", "content": "Мне одиноко и тяжело."}])
    assert res.status_code == 200
    assert res["Content-Type"].startswith("text/event-stream")
    body = b"".join(res.streaming_content).decode()

    assert "event: meta" in body
    assert "event: delta" in body
    assert "event: done" in body
    assert '"offline": true' in body  # test env has no API key → offline stub
    assert "disclaimer" in body


@pytest.mark.django_db
def test_support_stream_crisis_one_delta():
    acc = Account.objects.create_user(email="ai-crisis@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    res = _post_stream(client, [{"role": "user", "content": "хочу умереть"}])
    assert res.status_code == 200
    body = b"".join(res.streaming_content).decode()

    assert body.count("event: delta") == 1  # no typewriter over 112 instructions
    assert "112" in body
    assert '"crisis": true' in body


@pytest.mark.django_db
def test_support_stream_invalid_surface_400():
    acc = Account.objects.create_user(email="ai-bad@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    res = _post_stream(client, [{"role": "user", "content": "привет"}], surface="bogus")
    assert res.status_code == 400


@pytest.mark.django_db
def test_old_support_endpoint_untouched():
    acc = Account.objects.create_user(email="ai-old@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    res = client.post(
        "/api/v1/ai/support",
        data=json.dumps({"messages": [{"role": "user", "content": "Мне одиноко."}]}),
        content_type="application/json",
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["labeled_ai"] is True
    assert payload["disclaimer"]