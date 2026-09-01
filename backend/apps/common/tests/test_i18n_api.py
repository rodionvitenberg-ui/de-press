"""Endpoint tests for the UI-catalog translation API."""

from __future__ import annotations

import json

import pytest
from django.core.cache import cache
from django.test import Client

from api.v1.i18n import RATE_LIMIT
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


class _PerValueEcho:
    """Dedicated-mode fake: receives raw values, not JSON prompts."""

    def __init__(self) -> None:
        self.texts: list[str] = []

    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        self.texts.append(text)
        return f"DE:{text}"


class _StubEcho:
    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        return f"[offline {target_lang}] {text}"


class _GarbageEcho:
    """Mimics the model meta-explaining a short ambiguous word."""

    def translate(self, text: str, *, target_lang: str, source_lang: str = "") -> str:
        return (
            f"The word '{text}' refers to a list of recent items, "
            "derived from the verb 'to feed', commonly used in web UIs."
        )


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
def test_ui_catalog_second_load_served_from_cache(monkeypatch, settings):
    cache.clear()
    settings.TRANSLATOR_BASE_URL = ""  # env may set it; force the JSON-blob path
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


@pytest.mark.django_db
def test_ui_catalog_dedicated_translates_per_value(monkeypatch, settings):
    cache.clear()
    settings.TRANSLATOR_BASE_URL = "http://127.0.0.1:11434/v1"
    acc = Account.objects.create_user(email="i18n-pv@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    echo = _PerValueEcho()
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: echo)

    resp = _post_catalog(client, {"nav.feed": "Feed", "nav.chat": "Chat"})
    assert resp.status_code == 200
    assert resp.json()["strings"] == {
        "nav.feed": "DE:Feed",
        "nav.chat": "DE:Chat",
    }
    assert echo.texts == ["Feed", "Chat"]  # raw values, not a JSON blob


@pytest.mark.django_db
def test_ui_catalog_dedicated_stub_fails_honestly(monkeypatch, settings):
    cache.clear()
    settings.TRANSLATOR_BASE_URL = "http://127.0.0.1:11434/v1"
    acc = Account.objects.create_user(email="i18n-pvs@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: _StubEcho())

    resp = _post_catalog(client)
    assert resp.status_code == 400


@pytest.mark.django_db
def test_ui_catalog_dedicated_garbage_keeps_source(monkeypatch, settings):
    """One meta-explained string must not kill the whole language."""
    cache.clear()
    settings.TRANSLATOR_BASE_URL = "http://127.0.0.1:11434/v1"
    acc = Account.objects.create_user(email="i18n-gar@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: _GarbageEcho())

    resp = _post_catalog(client)
    assert resp.status_code == 200
    assert resp.json()["strings"] == {"nav.feed": "Feed"}  # source kept, no garbage

@pytest.mark.django_db
def test_ui_catalog_rate_limit_caps_language_loads(monkeypatch, settings):
    """RATE_LIMIT distinct catalog loads pass; the next one gets 429."""
    cache.clear()
    settings.TRANSLATOR_BASE_URL = ""  # env may set it; force the JSON-blob path
    acc = Account.objects.create_user(email="i18n-rl@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    monkeypatch.setattr("apps.common.i18n_ui.get_translator", lambda: _CountingEcho())

    statuses = []
    for i in range(RATE_LIMIT + 1):
        # Unique payload per call: catalog-cache hits bypass the rate limit.
        statuses.append(_post_catalog(client, {"nav.feed": f"Feed #{i}"}).status_code)

    assert statuses[:RATE_LIMIT] == [200] * RATE_LIMIT
    assert statuses[RATE_LIMIT] == 429
