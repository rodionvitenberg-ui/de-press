from __future__ import annotations

from uuid import UUID

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.identity.services import require_actor
from apps.moderation.blocks import (
    BlockError,
    block_actor,
    block_peer_in_dialogue,
    unblock_peer_in_dialogue,
)
from apps.moderation.models import ReportReason
from apps.moderation.services import ReportError, submit_message_report, submit_report
from apps.stories.services import StoryNotFound

router = Router(tags=["moderation"])


class DashboardOut(Schema):
    pending_clouds: int
    open_reports: int
    reviewing_reports: int
    reports_last_7d: int
    recent_reports: list[dict] = []


class ReportIn(Schema):
    reason: str
    details: str = ""


class ReportOut(Schema):
    ok: bool
    created: bool
    report_id: str
    message: str


class BlockIn(Schema):
    account_id: str | None = None
    session_id: str | None = None


class BlockOut(Schema):
    ok: bool
    created: bool
    message: str


@router.get("/moderation/dashboard", response=DashboardOut)
def helper_dashboard(request):
    """Сводка очередей и недавние репорты для хелперов (этичные метрики)."""
    actor = require_actor(request)
    if actor.account is None or not (
        actor.account.is_helper or actor.account.is_staff or actor.account.is_superuser
    ):
        raise HttpError(403, "Нужна роль Helper или staff")
    from apps.moderation.dashboard import build_dashboard

    view = build_dashboard()
    return DashboardOut(
        pending_clouds=view.pending_clouds,
        open_reports=view.open_reports,
        reviewing_reports=view.reviewing_reports,
        reports_last_7d=view.reports_last_7d,
        recent_reports=[
            {
                "id": r.id,
                "reason": r.reason,
                "status": r.status,
                "story_preview": r.story_preview,
                "details": r.details,
                "created_at": r.created_at,
            }
            for r in view.recent_reports
        ],
    )


@router.post("/stories/{story_id}/report", response=ReportOut)
def report_story(request, story_id: UUID, payload: ReportIn):
    actor = require_actor(request)
    if payload.reason not in ReportReason.values:
        raise HttpError(
            400,
            f"Invalid reason. Allowed: {', '.join(ReportReason.values)}",
        )
    try:
        result = submit_report(
            actor,
            story_id,
            reason=payload.reason,
            details=payload.details,
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except ReportError as exc:
        raise HttpError(400, str(exc)) from exc

    return ReportOut(
        ok=True,
        created=result.created,
        report_id=str(result.report.id),
        message=(
            "Жалоба принята. Спасибо, что помогаешь держать место безопасным."
            if result.created
            else "Ты уже отправлял жалобу на эту историю."
        ),
    )


@router.post("/messages/{message_id}/report", response=ReportOut)
def report_message(request, message_id: UUID, payload: ReportIn):
    actor = require_actor(request)
    if payload.reason not in ReportReason.values:
        raise HttpError(
            400,
            f"Invalid reason. Allowed: {', '.join(ReportReason.values)}",
        )
    try:
        result = submit_message_report(
            actor,
            message_id,
            reason=payload.reason,
            details=payload.details,
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except ReportError as exc:
        raise HttpError(400, str(exc)) from exc
    return ReportOut(
        ok=True,
        created=result.created,
        report_id=str(result.report.id),
        message=(
            "Жалоба на сообщение принята."
            if result.created
            else "Ты уже отправлял жалобу."
        ),
    )


@router.post("/blocks", response=BlockOut)
def create_block(request, payload: BlockIn):
    actor = require_actor(request)
    acc = UUID(payload.account_id) if payload.account_id else None
    sess = UUID(payload.session_id) if payload.session_id else None
    try:
        result = block_actor(
            actor,
            target_account_id=acc,
            target_session_id=sess,
        )
    except (BlockError, ValueError) as exc:
        raise HttpError(400, str(exc)) from exc
    return BlockOut(
        ok=True,
        created=result.created,
        message="Человек скрыт из твоей ленты." if result.created else "Уже в списке.",
    )


@router.post("/dialogues/{dialogue_id}/block-peer", response=BlockOut)
def block_dialogue_peer(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        result = block_peer_in_dialogue(actor, dialogue_id)
    except BlockError as exc:
        raise HttpError(400, str(exc)) from exc
    return BlockOut(
        ok=True,
        created=result.created,
        message=(
            "Собеседник скрыт. Новые запросы и истории от него не появятся."
            if result.created
            else "Уже в списке."
        ),
    )


@router.post("/dialogues/{dialogue_id}/unblock-peer", response=BlockOut)
def unblock_dialogue_peer(request, dialogue_id: UUID):
    actor = require_actor(request)
    try:
        removed = unblock_peer_in_dialogue(actor, dialogue_id)
    except BlockError as exc:
        raise HttpError(400, str(exc)) from exc
    return BlockOut(
        ok=True,
        created=removed > 0,
        message=(
            "Собеседник снова виден в ленте."
            if removed
            else "Он и так не был скрыт."
        ),
    )
