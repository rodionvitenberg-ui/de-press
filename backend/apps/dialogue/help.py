"""Help Request: visitor asks for a human Helper; Helper accepts → Dialogue without story."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.common.rate_limit import RateLimitExceeded, assert_under_limit
from apps.dialogue.models import (
    Dialogue,
    DialogueIntent,
    DialogueSource,
    DialogueStatus,
    HelpRequest,
    HelpRequestSkip,
    HelpRequestStatus,
    Message,
)
from apps.dialogue.services import RULES_TEXT
from apps.identity.models import Account
from apps.identity.services import Actor
from apps.moderation.blocks import is_blocked_between
from apps.notifications.models import NotificationKind
from apps.notifications.services import notify

HELP_CREATE_LIMIT = 5
HELP_CREATE_WINDOW_SECONDS = 3600

HELP_INTRO = (
    "[система] Кто-то попросил человека рядом. Ты Helper, не терапевт и не 112."
)


class HelpError(Exception):
    pass


def _is_helper(actor: Actor) -> bool:
    return bool(actor.account is not None and actor.account.is_helper)


def _requester_actor(req: HelpRequest) -> Actor:
    if req.from_account_id:
        return Actor(kind="account", account=req.from_account)
    return Actor(kind="anonymous", session=req.from_session)


def _pending_for_actor(actor: Actor) -> HelpRequest | None:
    if actor.account is not None:
        return (
            HelpRequest.objects.filter(
                from_account=actor.account,
                status=HelpRequestStatus.PENDING,
            )
            .order_by("-created_at")
            .first()
        )
    if actor.session is not None:
        return (
            HelpRequest.objects.filter(
                from_session=actor.session,
                status=HelpRequestStatus.PENDING,
            )
            .order_by("-created_at")
            .first()
        )
    return None


def _notify_helpers(req: HelpRequest, requester: Actor) -> None:
    payload = {"request_id": str(req.id)}
    helpers = Account.objects.filter(is_helper=True, is_active=True)
    for helper in helpers:
        if requester.account_id is not None and helper.id == requester.account_id:
            continue
        notify(
            Actor(kind="account", account=helper),
            NotificationKind.HELP_REQUESTED,
            payload,
        )


@transaction.atomic
def create_help_request(actor: Actor, *, note: str = "") -> HelpRequest:
    if actor.account is None and actor.session is None:
        raise HelpError("No identity")

    existing = _pending_for_actor(actor)
    if existing is not None:
        return existing

    try:
        assert_under_limit(
            actor=actor,
            queryset=HelpRequest.objects.all(),
            account_field="from_account",
            session_field="from_session",
            limit=HELP_CREATE_LIMIT,
            window_seconds=HELP_CREATE_WINDOW_SECONDS,
        )
    except RateLimitExceeded as exc:
        raise HelpError(str(exc)) from exc

    note_s = (note or "").strip()[:280]
    try:
        if actor.account is not None:
            req = HelpRequest.objects.create(
                from_account=actor.account,
                from_session=None,
                note=note_s,
                status=HelpRequestStatus.PENDING,
            )
        else:
            req = HelpRequest.objects.create(
                from_account=None,
                from_session=actor.session,
                note=note_s,
                status=HelpRequestStatus.PENDING,
            )
    except IntegrityError as exc:
        # Race: another create landed a pending row — return it idempotently.
        existing = _pending_for_actor(actor)
        if existing is not None:
            return existing
        raise HelpError("Could not create help request") from exc

    _notify_helpers(req, actor)
    return req


def list_help_inbox(actor: Actor) -> list[HelpRequest]:
    """Pending help requests visible to this Helper (excludes skips and own)."""
    if not _is_helper(actor):
        return []

    skipped_ids = HelpRequestSkip.objects.filter(helper=actor.account).values_list(
        "request_id", flat=True
    )
    # Null-safe own-request filter: anonymous rows have from_account_id NULL;
    # plain .exclude(from_account=...) can drop them under SQL three-valued logic.
    qs = (
        HelpRequest.objects.filter(status=HelpRequestStatus.PENDING)
        .exclude(id__in=skipped_ids)
        .filter(Q(from_account__isnull=True) | ~Q(from_account=actor.account))
        .select_related("from_account", "from_session")
        .order_by("-created_at")
    )
    return list(qs)


def my_help_request(actor: Actor) -> HelpRequest | None:
    """Pending request, else latest accepted-with-dialogue from the last 24h."""
    pending = _pending_for_actor(actor)
    if pending is not None:
        return pending

    since = timezone.now() - timedelta(hours=24)
    q = Q(status=HelpRequestStatus.ACCEPTED, dialogue__isnull=False, created_at__gte=since)
    if actor.account is not None:
        q &= Q(from_account=actor.account)
    elif actor.session is not None:
        q &= Q(from_session=actor.session)
    else:
        return None
    return (
        HelpRequest.objects.filter(q)
        .select_related("dialogue", "from_account", "from_session", "accepted_by")
        .order_by("-created_at")
        .first()
    )


@transaction.atomic
def accept_help_request(actor: Actor, request_id: UUID) -> Dialogue:
    if not _is_helper(actor):
        raise HelpError("Only a Helper can accept")

    try:
        req = (
            HelpRequest.objects.select_for_update(of=("self",))
            .select_related("from_account", "from_session")
            .get(pk=request_id)
        )
    except HelpRequest.DoesNotExist as exc:
        raise HelpError("Request not found") from exc

    if req.status != HelpRequestStatus.PENDING:
        raise HelpError("Request is not pending")

    if req.from_account_id is not None and req.from_account_id == actor.account_id:
        raise HelpError("Cannot accept own help request")

    requester = _requester_actor(req)
    if is_blocked_between(actor, requester):
        raise HelpError("Диалог недоступен")

    dialogue = Dialogue.objects.create(
        story=None,
        source=DialogueSource.HELP,
        author_account=req.from_account,
        author_session=req.from_session if req.from_account_id is None else None,
        peer_account=actor.account,
        peer_session=None,
        intent=DialogueIntent.LISTEN,
        status=DialogueStatus.OPEN,
    )
    Message.objects.create(
        dialogue=dialogue,
        body=f"[правила] {RULES_TEXT}",
        from_account=None,
        from_session=None,
    )
    Message.objects.create(
        dialogue=dialogue,
        body=HELP_INTRO,
        from_account=None,
        from_session=None,
    )
    note_s = (req.note or "").strip()
    if note_s:
        Message.objects.create(
            dialogue=dialogue,
            body=note_s,
            from_account=req.from_account,
            from_session=req.from_session if req.from_account_id is None else None,
        )

    req.status = HelpRequestStatus.ACCEPTED
    req.accepted_by = actor.account
    req.dialogue = dialogue
    req.save(update_fields=["status", "accepted_by", "dialogue", "updated_at"])

    notify(
        requester,
        NotificationKind.HELP_ACCEPTED,
        {"request_id": str(req.id), "dialogue_id": str(dialogue.id)},
    )
    return dialogue


@transaction.atomic
def skip_help_request(actor: Actor, request_id: UUID) -> HelpRequest:
    if not _is_helper(actor):
        raise HelpError("Only a Helper can skip")

    try:
        req = HelpRequest.objects.select_for_update(of=("self",)).get(pk=request_id)
    except HelpRequest.DoesNotExist as exc:
        raise HelpError("Request not found") from exc

    if req.status != HelpRequestStatus.PENDING:
        raise HelpError("Request is not pending")

    if req.from_account_id is not None and req.from_account_id == actor.account_id:
        raise HelpError("Cannot skip own help request")

    try:
        HelpRequestSkip.objects.create(request=req, helper=actor.account)
    except IntegrityError:
        # Already skipped — idempotent for this helper.
        pass
    return req


@transaction.atomic
def cancel_help_request(actor: Actor, request_id: UUID) -> HelpRequest:
    try:
        req = (
            HelpRequest.objects.select_for_update(of=("self",))
            .select_related("from_account", "from_session")
            .get(pk=request_id)
        )
    except HelpRequest.DoesNotExist as exc:
        raise HelpError("Request not found") from exc

    is_owner = False
    if actor.account is not None and req.from_account_id == actor.account_id:
        is_owner = True
    if actor.session is not None and req.from_session_id == actor.session_id:
        is_owner = True
    if not is_owner:
        raise HelpError("Only the requester can cancel")

    if req.status != HelpRequestStatus.PENDING:
        raise HelpError("Request is not pending")

    req.status = HelpRequestStatus.CANCELLED
    req.save(update_fields=["status", "updated_at"])
    return req
