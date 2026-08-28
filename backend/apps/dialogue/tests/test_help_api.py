"""HTTP contract for HelpRequest (visitor ask / Helper inbox)."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.test import Client

from apps.identity.models import Account


@pytest.fixture
def helper(db):
    return Account.objects.create_user(
        email="help-api-h@ex.com",
        password="password123",
        is_helper=True,
    )


@pytest.fixture
def helper2(db):
    return Account.objects.create_user(
        email="help-api-h2@ex.com",
        password="password123",
        is_helper=True,
    )


@pytest.fixture
def helper_client(helper):
    c = Client()
    c.force_login(helper)
    return c


@pytest.fixture
def helper2_client(helper2):
    c = Client()
    c.force_login(helper2)
    return c


@pytest.mark.django_db
def test_anon_create_helper_list_accept_second_fails_anon_list_403_cancel(
    helper_client, helper2_client
):
    anon = Client()
    created = anon.post(
        "/api/v1/help/requests",
        data={"note": "мне тяжело"},
        content_type="application/json",
    )
    assert created.status_code == 200
    body = created.json()
    assert body["note"] == "мне тяжело"
    assert body["status"] == "pending"
    assert body["dialogue_id"] is None
    assert "id" in body
    assert "created_at" in body
    assert settings.ANON_SESSION_COOKIE_NAME in anon.cookies
    req_id = body["id"]

    inbox = helper_client.get("/api/v1/help/requests")
    assert inbox.status_code == 200
    ids = [r["id"] for r in inbox.json()]
    assert req_id in ids

    accepted = helper_client.post(f"/api/v1/help/requests/{req_id}/accept")
    assert accepted.status_code == 200
    dialogue = accepted.json()
    assert dialogue["story_id"] is None
    assert dialogue["source"] == "help"

    second = helper2_client.post(f"/api/v1/help/requests/{req_id}/accept")
    assert second.status_code == 400

    forbidden = Client().get("/api/v1/help/requests")
    assert forbidden.status_code == 403


@pytest.mark.django_db
def test_cancel_then_helper_list_empty(helper_client):
    anon = Client()
    created = anon.post(
        "/api/v1/help/requests",
        data={"note": "отмена"},
        content_type="application/json",
    )
    assert created.status_code == 200
    req_id = created.json()["id"]

    cancelled = anon.post(f"/api/v1/help/requests/{req_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    inbox = helper_client.get("/api/v1/help/requests")
    assert inbox.status_code == 200
    assert inbox.json() == []
