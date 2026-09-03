from __future__ import annotations

from uuid import UUID

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.identity.services import require_actor
from apps.stories.services import StoryNotFound
from apps.support.services import (
    SupportError,
    approve_cloud,
    list_clouds_for_author,
    list_pending_queue,
    list_quiet_phrases,
    mark_clouds_read,
    reject_cloud,
    send_quiet_phrase,
    submit_moderated_cloud,
    dismiss_cloud,
)

router = Router(tags=["support"])


class QuietPhraseOut(Schema):
    key: str
    text: str
    image_url: str | None = None


class SendCloudIn(Schema):
    """Either phrase_key (Quiet Phrase) or body (Moderated / Helper free-text)."""

    phrase_key: str | None = None
    body: str | None = None


class SendCloudOut(Schema):
    ok: bool
    created: bool
    message: str
    cloud_id: str | None = None
    status: str | None = None


class SupportCloudOut(Schema):
    id: str
    body: str
    kind: str
    status: str
    pseudonym: str
    sender_ref: str
    helper_badge: str = ""
    is_priority: bool = False
    created_at: str
    image_url: str | None = None
    phrase_key: str = ""


class QueueCloudOut(SupportCloudOut):
    story_id: str
    story_preview: str


class ModerationOut(Schema):
    ok: bool
    status: str
    message: str
    cloud_id: str


class MarkCloudsReadOut(Schema):
    ok: bool = True
    cloud_unread: int = 0


def _cloud_out(c) -> SupportCloudOut:
    return SupportCloudOut(
        id=str(c.id),
        body=c.body,
        kind=c.kind,
        status=c.status,
        pseudonym=c.pseudonym,
        sender_ref=c.sender_ref,
        helper_badge=c.helper_badge,
        is_priority=c.is_priority,
        created_at=c.created_at,
        image_url=c.image_url,
        phrase_key=getattr(c, "phrase_key", "") or "",
    )


@router.get("/quiet-phrases", response=list[QuietPhraseOut])
def get_quiet_phrases(request, lang: str = "ru"):
    return [
        QuietPhraseOut(key=p.key, text=p.text, image_url=p.image_url)
        for p in list_quiet_phrases(lang=lang)
    ]


@router.post("/stories/{story_id}/clouds", response=SendCloudOut)
def post_cloud(request, story_id: UUID, payload: SendCloudIn):
    actor = require_actor(request)
    has_phrase = bool((payload.phrase_key or "").strip())
    has_body = bool((payload.body or "").strip())
    if has_phrase == has_body:
        raise HttpError(400, "Provide either phrase_key or body")

    try:
        if has_phrase:
            result = send_quiet_phrase(actor, story_id, payload.phrase_key or "")
            if result.created:
                msg = "Quiet cloud sent. Only the author will see it."
            else:
                msg = "This phrase has already been sent."
        else:
            result = submit_moderated_cloud(actor, story_id, payload.body or "")
            if result.cloud.status == "pending":
                msg = (
                    "Text sent for manual review. "
                    "The author will see it after approval."
                )
            else:
                msg = "Cloud delivered to the author (helper)."
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except SupportError as exc:
        raise HttpError(400, str(exc)) from exc

    return SendCloudOut(
        ok=True,
        created=result.created,
        message=msg,
        cloud_id=str(result.cloud.id),
        status=result.cloud.status,
    )


@router.post("/stories/{story_id}/clouds/mark-read", response=MarkCloudsReadOut)
def post_clouds_mark_read(request, story_id: UUID):
    actor = require_actor(request)
    try:
        mark_clouds_read(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except SupportError as exc:
        raise HttpError(403, str(exc)) from exc
    return MarkCloudsReadOut(ok=True, cloud_unread=0)


@router.get("/stories/{story_id}/clouds", response=list[SupportCloudOut])
def get_clouds(request, story_id: UUID):
    actor = require_actor(request)
    try:
        clouds = list_clouds_for_author(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except SupportError as exc:
        raise HttpError(403, str(exc)) from exc
    return [_cloud_out(c) for c in clouds]


@router.post(
    "/stories/{story_id}/clouds/{cloud_id}/dismiss",
    response=ModerationOut,
)
def post_dismiss_cloud(request, story_id: UUID, cloud_id: UUID):
    actor = require_actor(request)
    try:
        cloud = dismiss_cloud(actor, story_id, cloud_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except SupportError as exc:
        raise HttpError(403, str(exc)) from exc
    return ModerationOut(
        ok=True,
        status="dismissed",
        message="Cloud closed.",
        cloud_id=str(cloud.id),
    )


@router.get("/moderation/clouds", response=list[QueueCloudOut])
def get_moderation_queue(request):
    actor = require_actor(request)
    try:
        rows = list_pending_queue(actor)
    except SupportError as exc:
        raise HttpError(403, str(exc)) from exc
    return [
        QueueCloudOut(
            id=str(c.id),
            body=c.body,
            kind=c.kind,
            status=c.status,
            pseudonym=c.pseudonym,
            sender_ref=c.sender_ref,
            helper_badge=c.helper_badge,
            is_priority=c.is_priority,
            created_at=c.created_at,
            story_id=str(c.story_id),
            story_preview=c.story_preview,
        )
        for c in rows
    ]


@router.post("/moderation/clouds/{cloud_id}/approve", response=ModerationOut)
def post_approve(request, cloud_id: UUID):
    actor = require_actor(request)
    try:
        cloud = approve_cloud(actor, cloud_id)
    except SupportError as exc:
        code = 403 if "Helper" in str(exc) or "staff" in str(exc) else 400
        raise HttpError(code, str(exc)) from exc
    return ModerationOut(
        ok=True,
        status=cloud.status,
        message="Cloud delivered to the author.",
        cloud_id=str(cloud.id),
    )


@router.post("/moderation/clouds/{cloud_id}/reject", response=ModerationOut)
def post_reject(request, cloud_id: UUID):
    actor = require_actor(request)
    try:
        cloud = reject_cloud(actor, cloud_id)
    except SupportError as exc:
        code = 403 if "Helper" in str(exc) or "staff" in str(exc) else 400
        raise HttpError(code, str(exc)) from exc
    return ModerationOut(
        ok=True,
        status=cloud.status,
        message="Cloud rejected.",
        cloud_id=str(cloud.id),
    )
