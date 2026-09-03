from __future__ import annotations

from uuid import UUID

from ninja import File, Form, Router, Schema
from ninja.errors import HttpError
from ninja.files import UploadedFile as NinjaUploadedFile

from apps.empathy.services import ensure_pulse
from apps.identity.services import require_actor, resolve_actor
from apps.stories.models import StoryStatus
from apps.stories.realtime import audio_url_for, author_key_for
from apps.support.services import (
    ReceivedCloudView,
    cloud_gestures_for_roots,
    cloud_unread_for_roots,
    my_phrase_keys_for,
    received_clouds_for_author,
)
from apps.stories.services import (
    StoryError,
    StoryNotFound,
    StoryPermissionError,
    add_comment,
    add_comment_voice,
    delete_story,
    edit_story,
    get_story,
    hide_story,
    is_author,
    list_author_stories,
    list_feed,
    list_story_thread,
    publish_story,
    publish_story_voice,
    topic_choices,
    unhide_story,
)

router = Router(tags=["stories"])


class ReceivedCloudOut(Schema):
    id: str
    phrase_key: str = ""
    body: str = ""


class StoryOut(Schema):
    id: str
    body: str
    topic: str
    pseudonym: str
    published_at: str | None
    status: str
    is_mine: bool = False
    author_key: str = ""
    parent_id: str | None = None
    my_phrase_key: str = ""
    cloud_unread: int = 0
    cloud_gesture: str = ""
    received_clouds: list[ReceivedCloudOut] = []
    audio_url: str | None = None
    duration_ms: int | None = None


class StoryCreateIn(Schema):
    body: str
    pseudonym: str | None = None
    topic: str | None = None


class StoryEditIn(Schema):
    body: str


class FeedOut(Schema):
    items: list[StoryOut]
    next_cursor: str | None


class AuthorStoryOut(Schema):
    id: str
    body: str
    topic: str
    pseudonym: str
    published_at: str | None
    status: str
    pulse_count: int
    pulse_message: str
    author_key: str = ""
    cloud_unread: int = 0
    cloud_gesture: str = ""
    audio_url: str | None = None
    duration_ms: int | None = None


class TopicOut(Schema):
    value: str
    label: str


def _received_out(rows: list[ReceivedCloudView]) -> list[ReceivedCloudOut]:
    return [
        ReceivedCloudOut(id=r.id, phrase_key=r.phrase_key, body=r.body) for r in rows
    ]


def _story_out(
    story,
    actor=None,
    *,
    my_keys: dict | None = None,
    unread: dict | None = None,
    gestures: dict | None = None,
    received: dict | None = None,
) -> StoryOut:
    mine = bool(actor is not None and is_author(story, actor))
    root_mine = mine and not story.parent_id
    return StoryOut(
        id=str(story.id),
        body=story.body,
        topic=story.topic,
        pseudonym=story.pseudonym_snapshot,
        published_at=story.published_at.isoformat() if story.published_at else None,
        status=story.status,
        is_mine=mine,
        author_key=author_key_for(story),
        parent_id=str(story.parent_id) if story.parent_id else None,
        my_phrase_key=(my_keys or {}).get(story.id, ""),
        cloud_unread=(unread or {}).get(story.id, 0) if root_mine else 0,
        cloud_gesture=(gestures or {}).get(story.id, "") if root_mine else "",
        received_clouds=_received_out((received or {}).get(story.id, []) if mine else []),
        audio_url=audio_url_for(story),
        duration_ms=story.duration_ms,
    )


def _cloud_maps(stories, actor, *, with_received: bool = False):
    ids = [s.id for s in stories]
    my_keys = my_phrase_keys_for(actor, ids)
    roots = [s for s in stories if not s.parent_id]
    unread = cloud_unread_for_roots(actor, roots)
    gestures = cloud_gestures_for_roots(actor, roots)
    received = received_clouds_for_author(actor, ids) if with_received else {}
    return my_keys, unread, gestures, received


@router.get("/topics", response=list[TopicOut])
def topics(request):
    return [TopicOut(**t) for t in topic_choices()]


@router.get("/stories", response=FeedOut)
def feed(
    request,
    cursor: str | None = None,
    limit: int = 20,
    topic: str | None = None,
):
    viewer = resolve_actor(request)
    page = list_feed(cursor=cursor, limit=limit, topic=topic, viewer=viewer)
    my_keys, unread, gestures, received = _cloud_maps(page.items, viewer)
    return FeedOut(
        items=[
            _story_out(
                s,
                viewer,
                my_keys=my_keys,
                unread=unread,
                gestures=gestures,
                received=received,
            )
            for s in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.post("/stories/voice", response=StoryOut)
def story_create_voice(
    request,
    audio: NinjaUploadedFile = File(...),
    body: str = Form(""),
    topic: str | None = Form(None),
    pseudonym: str | None = Form(None),
    duration_ms: int | None = Form(None),
    source_lang: str = Form("ru"),
):
    actor = require_actor(request)
    try:
        story = publish_story_voice(
            actor,
            body or "",
            uploaded_file=audio,
            duration_ms=duration_ms,
            pseudonym=pseudonym,
            topic=topic,
            source_lang=source_lang or "ru",
        )
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


@router.get("/stories/{story_id}", response=StoryOut)
def story_detail(request, story_id: UUID):
    actor = resolve_actor(request)
    try:
        story = get_story(story_id, for_public=False)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    if story.status == StoryStatus.REMOVED:
        raise HttpError(404, "Story not found")
    if story.status != StoryStatus.PUBLISHED:
        if actor is None or not is_author(story, actor):
            raise HttpError(404, "Story not found")
    my_keys, unread, gestures, received = _cloud_maps([story], actor)
    return _story_out(
        story,
        actor,
        my_keys=my_keys,
        unread=unread,
        gestures=gestures,
        received=received,
    )


class ThreadOut(Schema):
    items: list[StoryOut]


@router.get("/stories/{story_id}/thread", response=ThreadOut)
def story_thread(request, story_id: UUID):
    actor = resolve_actor(request)
    try:
        rows = list_story_thread(story_id, viewer=actor)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    my_keys, unread, gestures, received = _cloud_maps(rows, actor, with_received=True)
    return ThreadOut(
        items=[
            _story_out(
                s,
                actor,
                my_keys=my_keys,
                unread=unread,
                gestures=gestures,
                received=received,
            )
            for s in rows
        ]
    )


@router.patch("/stories/{story_id}", response=StoryOut)
def story_patch(request, story_id: UUID, payload: StoryEditIn):
    actor = require_actor(request)
    try:
        story = edit_story(actor, story_id, payload.body)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except StoryPermissionError as exc:
        raise HttpError(403, str(exc)) from exc
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


def _story_status_action(request, story_id: UUID, fn):
    actor = require_actor(request)
    try:
        story = fn(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except StoryPermissionError as exc:
        raise HttpError(403, str(exc)) from exc
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


@router.post("/stories/{story_id}/hide", response=StoryOut)
def story_hide(request, story_id: UUID):
    return _story_status_action(request, story_id, hide_story)


@router.post("/stories/{story_id}/unhide", response=StoryOut)
def story_unhide(request, story_id: UUID):
    return _story_status_action(request, story_id, unhide_story)


@router.delete("/stories/{story_id}", response=StoryOut)
def story_remove(request, story_id: UUID):
    return _story_status_action(request, story_id, delete_story)


@router.post("/stories/{story_id}/comments", response=StoryOut)
def story_comment(request, story_id: UUID, payload: StoryEditIn):
    actor = require_actor(request)
    try:
        story = add_comment(actor, story_id, payload.body)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except StoryPermissionError as exc:
        raise HttpError(403, str(exc)) from exc
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


@router.post("/stories", response=StoryOut)
def story_create(request, payload: StoryCreateIn):
    actor = require_actor(request)
    try:
        story = publish_story(
            actor,
            payload.body,
            pseudonym=payload.pseudonym,
            topic=payload.topic,
        )
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


@router.post("/stories/{story_id}/comments/voice", response=StoryOut)
def story_comment_voice(
    request,
    story_id: UUID,
    audio: NinjaUploadedFile = File(...),
    body: str = Form(""),
    duration_ms: int | None = Form(None),
    source_lang: str = Form("ru"),
):
    actor = require_actor(request)
    try:
        story = add_comment_voice(
            actor,
            story_id,
            body or "",
            uploaded_file=audio,
            duration_ms=duration_ms,
            source_lang=source_lang or "ru",
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except StoryPermissionError as exc:
        raise HttpError(403, str(exc)) from exc
    except StoryError as exc:
        raise HttpError(400, str(exc)) from exc
    return _story_out(story, actor)


@router.get("/me/stories", response=list[AuthorStoryOut])
def my_stories(request):
    actor = require_actor(request)
    stories = list(list_author_stories(actor))
    unread = cloud_unread_for_roots(actor, stories)
    gestures = cloud_gestures_for_roots(actor, stories)
    rows = []
    for story in stories:
        pulse = ensure_pulse(story)
        count = pulse.count
        rows.append(
            AuthorStoryOut(
                id=str(story.id),
                body=story.body,
                topic=story.topic,
                pseudonym=story.pseudonym_snapshot,
                published_at=story.published_at.isoformat() if story.published_at else None,
                status=story.status,
                author_key=author_key_for(story),
                pulse_count=count,
                pulse_message=(
                    f"{count} people read this and sat with you silently."
                    if count
                    else "Quiet so far. That is okay too."
                ),
                cloud_unread=unread.get(story.id, 0),
                cloud_gesture=gestures.get(story.id, ""),
                audio_url=audio_url_for(story),
                duration_ms=story.duration_ms,
            )
        )
    return rows
