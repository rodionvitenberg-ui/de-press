"""Tests through stories/empathy service interfaces."""

from __future__ import annotations

import pytest

from apps.empathy.services import get_pulse_for_author, offer_empathy
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.stories.services import list_feed, publish_story, publish_story_voice


@pytest.mark.django_db
def test_publish_and_feed():
    account = Account.objects.create_user(email="a@example.com", password="password123")
    actor = Actor(kind="account", account=account)
    story = publish_story(actor, "Сегодня тяжело, но я здесь.", topic="anxiety")
    page = list_feed(topic="anxiety")
    assert len(page.items) == 1
    assert page.items[0].id == story.id
    assert page.items[0].topic == "anxiety"
    assert page.items[0].pseudonym_snapshot == account.display_pseudonym


@pytest.mark.django_db
def test_silent_empathy_idempotent():
    account = Account.objects.create_user(email="author@example.com", password="password123")
    author = Actor(kind="account", account=account)
    story = publish_story(author, "Мне нужно, чтобы кто-то просто был рядом.")

    session = AnonymousSession.objects.create(pseudonym="слушатель")
    visitor = Actor(kind="anonymous", session=session)

    first = offer_empathy(visitor, story.id)
    second = offer_empathy(visitor, story.id)
    assert first.created is True
    assert second.created is False
    from apps.notifications.models import Notification

    assert Notification.objects.filter(
        kind="silent_empathy",
        recipient_account=account,
        payload__story_id=str(story.id),
    ).count() == 1

    pulse = get_pulse_for_author(author, story.id)
    assert pulse == 1


@pytest.mark.django_db
def test_author_edit_hide_unhide_delete():
    from apps.stories.models import StoryStatus
    from apps.stories.services import (
        StoryPermissionError,
        delete_story,
        edit_story,
        hide_story,
        list_feed,
        unhide_story,
    )

    account = Account.objects.create_user(email="own@ex.com", password="password123")
    author = Actor(kind="account", account=account)
    other = Actor(
        kind="account",
        account=Account.objects.create_user(email="x@ex.com", password="password123"),
    )
    story = publish_story(author, "Черновик мысли.")
    edited = edit_story(author, story.id, "Уже иначе.")
    assert edited.body == "Уже иначе."
    with pytest.raises(StoryPermissionError):
        edit_story(other, story.id, "хак")

    hide_story(author, story.id)
    assert list_feed().items == []
    unhide_story(author, story.id)
    assert list_feed().items[0].id == story.id

    delete_story(author, story.id)
    story.refresh_from_db()
    assert story.status == StoryStatus.REMOVED
    assert list_feed().items == []


def _note() -> SimpleUploadedFile:
    return SimpleUploadedFile(
        "note.webm",
        b"\x1a\x45\xdf\xa3fake-webm-bytes",
        content_type="audio/webm",
    )


@pytest.mark.django_db
def test_publish_voice_only_keeps_empty_body(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    account = Account.objects.create_user(email="v@ex.com", password="password123")
    actor = Actor(kind="account", account=account)
    story = publish_story_voice(
        actor,
        "",
        uploaded_file=_note(),
        duration_ms=1500,
        topic="anxiety",
    )
    assert story.audio
    assert story.duration_ms == 1500
    assert story.body == ""  # voice transcription is removed


@pytest.mark.django_db
def test_publish_text_plus_voice_keeps_typed_body(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    account = Account.objects.create_user(email="tv@ex.com", password="password123")
    actor = Actor(kind="account", account=account)
    story = publish_story_voice(
        actor,
        "Сама написала.",
        uploaded_file=_note(),
        duration_ms=800,
    )
    assert story.body == "Сама написала."
    assert story.audio


@pytest.mark.django_db
def test_publish_voice_rejects_empty_both():
    from apps.stories.services import StoryError

    account = Account.objects.create_user(email="e@ex.com", password="password123")
    actor = Actor(kind="account", account=account)
    with pytest.raises(StoryError, match="empty"):
        publish_story(actor, "   ")


@pytest.mark.django_db
def test_comment_voice_author_only(tmp_path, settings):
    from apps.stories.services import StoryPermissionError, add_comment_voice

    settings.MEDIA_ROOT = tmp_path
    author_acc = Account.objects.create_user(email="ca@ex.com", password="password123")
    author = Actor(kind="account", account=author_acc)
    other = Actor(
        kind="account",
        account=Account.objects.create_user(email="co@ex.com", password="password123"),
    )
    post = publish_story(author, "корень")
    with pytest.raises(StoryPermissionError):
        add_comment_voice(other, post.id, "", uploaded_file=_note(), duration_ms=400)
    comment = add_comment_voice(
        author, post.id, "", uploaded_file=_note(), duration_ms=400
    )
    assert comment.parent_id == post.id
    assert comment.audio


@pytest.mark.django_db
def test_delete_story_removes_audio_file(tmp_path, settings):
    from pathlib import Path

    from apps.stories.services import delete_story

    settings.MEDIA_ROOT = tmp_path
    account = Account.objects.create_user(email="d@ex.com", password="password123")
    actor = Actor(kind="account", account=account)
    story = publish_story_voice(
        actor, "с файлом", uploaded_file=_note(), duration_ms=200
    )
    path = Path(story.audio.path)
    assert path.exists()
    delete_story(actor, story.id)
    assert not path.exists()
    story.refresh_from_db()
    from apps.stories.models import StoryStatus

    assert story.status == StoryStatus.REMOVED
    assert list_feed().items == []


@pytest.mark.django_db
def test_feed_one_row_per_post_comment_bumps():
    from apps.stories.services import (
        StoryPermissionError,
        add_comment,
        list_story_thread,
    )

    a = Actor(
        kind="account",
        account=Account.objects.create_user(email="mono@ex.com", password="password123"),
    )
    b = Actor(
        kind="account",
        account=Account.objects.create_user(email="other@ex.com", password="password123"),
    )
    first = publish_story(a, "Первая мысль.")
    other = publish_story(b, "Чужая.")
    page = list_feed()
    assert [s.id for s in page.items] == [other.id, first.id]

    second = publish_story(a, "Ещё одна.")
    page = list_feed()
    assert [s.id for s in page.items] == [second.id, other.id, first.id]
    thread = list_story_thread(second.id)
    assert [s.id for s in thread] == [second.id]

    comment = add_comment(a, first.id, "дописал к первой")
    assert comment.parent_id == first.id
    page = list_feed()
    assert [s.id for s in page.items] == [first.id, second.id, other.id]
    assert all(s.id != comment.id for s in page.items)
    thread = list_story_thread(first.id)
    assert [s.id for s in thread] == [first.id, comment.id]
    with pytest.raises(StoryPermissionError):
        add_comment(b, first.id, "чужой коммент")


@pytest.mark.django_db
def test_publish_session_author_and_list_mine():
    from apps.stories.services import StoryError, list_author_stories, topic_choices

    sess = AnonymousSession.objects.create(pseudonym="гость")
    actor = Actor(kind="anonymous", session=sess)
    story = publish_story(actor, "анонимно", topic="grief")
    assert story.author_session_id == sess.id
    mine = list_author_stories(actor)
    assert mine[0].id == story.id
    assert any(t["value"] == "grief" for t in topic_choices())
    with pytest.raises(StoryError):
        publish_story(actor, "   ")
    with pytest.raises(StoryError):
        publish_story(actor, "ok", topic="not-a-topic")
    empty = Actor(kind="anonymous", session=None)
    with pytest.raises(StoryError):
        publish_story(empty, "нет личности")
    assert list_author_stories(empty) == []


@pytest.mark.django_db
def test_moderate_and_get_story_errors():
    from uuid import uuid4

    from apps.stories.models import StoryStatus
    from apps.stories.services import (
        StoryError,
        StoryNotFound,
        get_story,
        moderate_story,
    )

    account = Account.objects.create_user(email="mod@ex.com", password="password123")
    story = publish_story(Actor(kind="account", account=account), "модерация")
    hidden = moderate_story(story.id, StoryStatus.HIDDEN)
    assert hidden.status == StoryStatus.HIDDEN
    with pytest.raises(StoryNotFound):
        get_story(story.id, for_public=True)
    with pytest.raises(StoryError):
        moderate_story(story.id, "nope")
    with pytest.raises(StoryNotFound):
        moderate_story(uuid4(), StoryStatus.PUBLISHED)

