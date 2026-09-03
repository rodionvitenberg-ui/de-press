"""Tests through empathy module interface (Pulse, Hearers, consent)."""

from __future__ import annotations

import pytest

from apps.empathy.services import (
    EmpathyError,
    list_hearers_for_author,
    offer_empathy,
    set_outreach_consent,
)
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.stories.services import publish_story


@pytest.mark.django_db
def test_list_hearers_author_only():
    author_acc = Account.objects.create_user(
        email="author-h@ex.com", password="password123", default_pseudonym="автор"
    )
    author = Actor(kind="account", account=author_acc)
    story = publish_story(author, "История для hearers.")

    peer = Actor(
        kind="anonymous",
        session=AnonymousSession.objects.create(pseudonym="слушатель"),
    )
    offer_empathy(peer, story.id)

    hearers = list_hearers_for_author(author, story.id)
    assert len(hearers) == 1
    assert hearers[0].pseudonym == "слушатель"
    assert hearers[0].outreach_opt_in is True
    assert hearers[0].hearer_ref.startswith("session:")
    assert hearers[0].has_open_dialogue is False

    stranger = Actor(
        kind="anonymous", session=AnonymousSession.objects.create(pseudonym="чужой")
    )
    with pytest.raises(EmpathyError, match="author"):
        list_hearers_for_author(stranger, story.id)


@pytest.mark.django_db
def test_empathy_http_offer_and_pulse():
    from django.test import Client

    author_acc = Account.objects.create_user(
        email="emp-api@ex.com", password="password123"
    )
    author = Actor(kind="account", account=author_acc)
    story = publish_story(author, "для лучей")
    visitor = Account.objects.create_user(
        email="hear-api@ex.com", password="password123"
    )
    client = Client()
    client.force_login(visitor)
    res = client.post(f"/api/v1/stories/{story.id}/empathy")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    owner = Client()
    owner.force_login(author_acc)
    pulse = owner.get(f"/api/v1/stories/{story.id}/pulse")
    assert pulse.status_code == 200
    assert pulse.json()["count"] == 1
    hearers = owner.get(f"/api/v1/stories/{story.id}/hearers")
    assert hearers.status_code == 200
    assert len(hearers.json()) == 1


@pytest.mark.django_db
def test_outreach_consent_opt_out():
    author_acc = Account.objects.create_user(email="a-c@ex.com", password="password123")
    author = Actor(kind="account", account=author_acc)
    story = publish_story(author, "Текст.")

    peer_sess = AnonymousSession.objects.create(pseudonym="п")
    peer = Actor(kind="anonymous", session=peer_sess)
    offer_empathy(peer, story.id)

    assert set_outreach_consent(peer, story.id, opt_in=False) is False
    hearers = list_hearers_for_author(author, story.id)
    assert hearers[0].outreach_opt_in is False

    assert set_outreach_consent(peer, story.id, opt_in=True) is True
