from __future__ import annotations

import pytest
from django.core.cache import cache

from apps.ai.crisis import looks_like_crisis
from apps.ai.services import AIError, support_chat
from apps.identity.models import AnonymousSession
from apps.identity.services import Actor


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_crisis_detection():
    assert looks_like_crisis("я не хочу жить")
    assert not looks_like_crisis("мне просто грустно сегодня")


@pytest.mark.django_db
def test_offline_support_reply():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    result = support_chat(
        actor,
        messages=[{"role": "user", "content": "Мне одиноко и тяжело."}],
        surface="companion",
    )
    assert result.labeled_ai is True
    assert result.crisis is False
    assert len(result.reply) > 10


@pytest.mark.django_db
def test_crisis_short_circuit():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    result = support_chat(
        actor,
        messages=[{"role": "user", "content": "хочу умереть"}],
        surface="companion",
    )
    assert result.crisis is True
    assert "112" in result.reply


@pytest.mark.django_db
def test_requires_user_message():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    with pytest.raises(AIError):
        support_chat(actor, messages=[{"role": "assistant", "content": "hi"}])
