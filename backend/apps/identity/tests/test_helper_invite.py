from __future__ import annotations

from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.identity.invites import (
    InviteError,
    accept_helper_invite,
    create_helper_invite,
)
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor


@pytest.mark.django_db
def test_helper_creates_invite_account_accepts():
    helper = Account.objects.create_user(
        email="inviter@ex.com", password="password123", is_helper=True, helper_org="pilot"
    )
    invite = create_helper_invite(Actor(kind="account", account=helper), org="ngo")
    assert invite.org == "ngo"
    assert invite.used_at is None

    candidate = Account.objects.create_user(
        email="newh@ex.com", password="password123"
    )
    acc = accept_helper_invite(
        Actor(kind="account", account=candidate), invite.token, pledge=True
    )
    assert acc.is_helper is True
    assert acc.helper_org == "ngo"
    invite.refresh_from_db()
    assert invite.used_by_id == candidate.id


@pytest.mark.django_db
def test_visitor_cannot_accept():
    helper = Account.objects.create_user(
        email="inv2@ex.com", password="password123", is_helper=True
    )
    invite = create_helper_invite(Actor(kind="account", account=helper))
    sess = AnonymousSession.objects.create()
    with pytest.raises(InviteError):
        accept_helper_invite(
            Actor(kind="anonymous", session=sess), invite.token, pledge=True
        )


@pytest.mark.django_db
def test_expired_and_used_and_no_pledge():
    helper = Account.objects.create_user(
        email="inv3@ex.com", password="password123", is_helper=True
    )
    actor = Actor(kind="account", account=helper)
    invite = create_helper_invite(actor, ttl_hours=1)
    invite.expires_at = timezone.now() - timedelta(minutes=1)
    invite.save(update_fields=["expires_at"])
    cand = Account.objects.create_user(email="late@ex.com", password="password123")
    with pytest.raises(InviteError):
        accept_helper_invite(Actor(kind="account", account=cand), invite.token, pledge=True)

    invite2 = create_helper_invite(actor)
    with pytest.raises(InviteError):
        accept_helper_invite(
            Actor(kind="account", account=cand), invite2.token, pledge=False
        )


@pytest.mark.django_db
def test_non_helper_cannot_create_http():
    acc = Account.objects.create_user(email="plain@ex.com", password="password123")
    client = Client()
    client.force_login(acc)
    res = client.post(
        "/api/v1/helper-invites",
        data={"org": "x"},
        content_type="application/json",
    )
    assert res.status_code == 403


@pytest.mark.django_db
def test_http_create_and_accept():
    helper = Account.objects.create_user(
        email="http-h@ex.com", password="password123", is_helper=True
    )
    inviter = Client()
    inviter.force_login(helper)
    created = inviter.post(
        "/api/v1/helper-invites",
        data={"org": "haven", "ttl_hours": 24},
        content_type="application/json",
    )
    assert created.status_code == 200
    token = created.json()["token"]
    listed = inviter.get("/api/v1/helper-invites")
    assert listed.status_code == 200
    assert any(row["token"] == token for row in listed.json())

    cand = Account.objects.create_user(email="http-c@ex.com", password="password123")
    joiner = Client()
    joiner.force_login(cand)
    preview = joiner.get(f"/api/v1/helper-invites/{token}")
    assert preview.status_code == 200
    assert preview.json()["org"] == "haven"

    accepted = joiner.post(
        f"/api/v1/helper-invites/{token}/accept",
        data={"pledge": True},
        content_type="application/json",
    )
    assert accepted.status_code == 200
    cand.refresh_from_db()
    assert cand.is_helper is True
    assert cand.is_on_duty is False
    me = joiner.get("/api/v1/me").json()
    assert me["is_helper"] is True
    assert me["is_staff"] is False
    assert me["is_on_duty"] is False
