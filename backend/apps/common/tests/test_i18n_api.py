"""Endpoint tests for the UI-catalog translation API."""

from __future__ import annotations

import json

import pytest
from django.core.cache import cache
from django.test import Client

from apps.identity.models import Account


class _CountingEcho:
    def __init__(self) -> None:
        self.calls = 0

    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        self.calls += 1
        start = text.find('{"')
        end = text.rfind("}")
        data = json.loads(text[start : end + 1])
        return json.dumps({k: f"DE:{v}" for k, v in data.items()}, ensure_ascii=False)


def _post_catalog(client: Client, strings: dict[str, str] | None = None):
    return client.post(
        "/api/v1/i18n/ui-catalog",
        data=json.dumps(
            {
                "target_lang": "de",
                "source_lang": "en",
                "strings": strings or {"nav.feed": "Feed"},
            }
        ),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_ui_catalog_second_load_served_from_cache(monkeypatch):
    cache.clear()
    acc = Account.objects.create_user(email="i18n-c@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    echo = _CountingEcho()
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: echo)

    first = _post_catalog(client)
    assert first.status_code == 200
    assert first.json()["strings"] == {"nav.feed": "DE:Feed"}

    second = _post_catalog(client)  # identical payload → cache hit
    assert second.status_code == 200
    assert second.json() == first.json()
    assert echo.calls == 1  # translator ran only once
