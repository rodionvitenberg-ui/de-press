from __future__ import annotations

import pytest
from django.core.cache import cache

from apps.ai.crisis import looks_like_crisis
from apps.ai.services import AI_LIMIT, AIError, stream_support_chat, support_chat
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


@pytest.mark.django_db
def test_stream_offline_single_chunk():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    stream = stream_support_chat(
        actor,
        messages=[{"role": "user", "content": "Мне одиноко и тяжело."}],
        surface="companion",
    )
    assert stream.offline is True
    assert stream.crisis is False
    chunks = list(stream.chunks)
    assert len(chunks) == 1  # offline stub — one piece
    assert len(chunks[0]) > 10


@pytest.mark.django_db
def test_stream_crisis_single_piece_no_typewriter():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    stream = stream_support_chat(
        actor,
        messages=[{"role": "user", "content": "хочу умереть"}],
        surface="companion",
    )
    assert stream.crisis is True
    chunks = list(stream.chunks)
    assert len(chunks) == 1
    assert "112" in chunks[0]


@pytest.mark.django_db
def test_stream_validation_is_eager():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    with pytest.raises(AIError):
        stream_support_chat(
            actor,
            messages=[{"role": "assistant", "content": "hi"}],
            surface="companion",
        )
    with pytest.raises(AIError):
        stream_support_chat(
            actor,
            messages=[{"role": "user", "content": "привет"}],
            surface="bogus",
        )


@pytest.mark.django_db
def test_stream_rate_limited():
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    cache.set(f"ai_rl:sess:{session.id}", AI_LIMIT, timeout=60)
    with pytest.raises(AIError):
        stream_support_chat(
            actor,
            messages=[{"role": "user", "content": "привет"}],
            surface="companion",
        )


@pytest.mark.django_db
def test_stream_gateway_failure_surfaces_as_aierror(monkeypatch):
    from apps.ai import services as ai_services

    class ExplodingGateway:
        is_offline = False

        def complete(self, messages: list) -> str:
            return "ok"

        def stream(self, messages: list):
            raise RuntimeError("provider down")
            yield ""  # pragma: no cover — make it a generator

    monkeypatch.setattr(ai_services, "get_gateway", lambda: ExplodingGateway())
    session = AnonymousSession.objects.create()
    actor = Actor(kind="anonymous", session=session)
    stream = ai_services.stream_support_chat(
        actor,
        messages=[{"role": "user", "content": "привет"}],
        surface="companion",
    )
    with pytest.raises(AIError):
        list(stream.chunks)
