"""API + identity tests for bug reports."""

from __future__ import annotations

import json

import pytest
from django.test import Client

from apps.common.models import BugReport
from apps.identity.models import Account


def _post_bug(client: Client, text: str = "Кнопка сохранения не работает"):
    return client.post(
        "/api/v1/bugs",
        data=json.dumps({"text": text, "page": "/more"}),
        content_type="application/json",
        HTTP_USER_AGENT="test-agent",
    )


@pytest.mark.django_db
def test_bug_report_account_identity_and_fields():
    acc = Account.objects.create_user(email="bug-a@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    resp = _post_bug(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True

    bug = BugReport.objects.get(id=data["id"])
    assert bug.reporter_account_id == acc.id
    assert bug.reporter_session_id is None
    assert bug.status == BugReport.Status.NEW
    assert bug.page == "/more"
    assert bug.user_agent == "test-agent"


@pytest.mark.django_db
def test_bug_report_anonymous_mints_session():
    client = Client()

    resp = _post_bug(client, text="Лента пустая после рефреша")
    assert resp.status_code == 200

    bug = BugReport.objects.get(id=resp.json()["id"])
    assert bug.reporter_account_id is None
    assert bug.reporter_session_id is not None


@pytest.mark.django_db
def test_bug_report_validation():
    acc = Account.objects.create_user(email="bug-v@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    assert _post_bug(client, text="   ").status_code == 400
    assert _post_bug(client, text="x" * 4001).status_code == 400
    assert BugReport.objects.count() == 0


@pytest.mark.django_db
def test_bug_report_rate_limited():
    acc = Account.objects.create_user(email="bug-r@ex.com", password="password123")
    client = Client()
    client.force_login(acc)

    for _ in range(10):
        assert _post_bug(client).status_code == 200
    assert _post_bug(client).status_code == 400  # rate limit wrapped as BugReportError
    assert BugReport.objects.count() == 10
