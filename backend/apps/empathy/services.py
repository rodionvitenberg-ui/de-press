"""Deep empathy module: offer Silent Empathy, read Pulse, Hearer List."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import F

from apps.common.rate_limit import RateLimitExceeded, assert_under_limit
from apps.empathy.models import EmpathyPulse, SilentEmpathy
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.stories.models import Story
from apps.stories.services import StoryNotFound, get_story, is_author

EMPATHY_LIMIT = 60
EMPATHY_WINDOW_SECONDS = 3600


class EmpathyError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OfferResult:
    created: bool
    pulse_count: int | None  # only for author; usually None for offerer
    outreach_opt_in: bool


@dataclass(frozen=True, slots=True)
class HearerView:
    hearer_ref: str
    pseudonym: str
    outreach_opt_in: bool
    created_at: str
    has_open_dialogue: bool


def ensure_pulse(story: Story) -> EmpathyPulse:
    pulse, _ = EmpathyPulse.objects.get_or_create(story=story)
    return pulse


def hearer_ref_for_empathy(row: SilentEmpathy) -> str:
    if row.from_account_id:
        return f"account:{row.from_account_id}"
    return f"session:{row.from_session_id}"


def parse_hearer_ref(ref: str) -> tuple[str, UUID]:
    """Return (kind, id) for account:… or session:…"""
    raw = (ref or "").strip()
    if ":" not in raw:
        raise EmpathyError("Invalid hearer_ref")
    kind, id_s = raw.split(":", 1)
    if kind not in ("account", "session"):
        raise EmpathyError("Invalid hearer_ref")
    try:
        return kind, UUID(id_s)
    except ValueError as exc:
        raise EmpathyError("Invalid hearer_ref") from exc


def actor_from_hearer_ref(ref: str) -> Actor:
    kind, uid = parse_hearer_ref(ref)
    if kind == "account":
        try:
            account = Account.objects.get(pk=uid)
        except Account.DoesNotExist as exc:
            raise EmpathyError("Hearer not found") from exc
        return Actor(kind="account", account=account)
    try:
        session = AnonymousSession.objects.get(pk=uid)
    except AnonymousSession.DoesNotExist as exc:
        raise EmpathyError("Hearer not found") from exc
    return Actor(kind="anonymous", session=session)


def _pseudonym_for_empathy(row: SilentEmpathy) -> str:
    if row.from_account_id and row.from_account is not None:
        return row.from_account.display_pseudonym
    if row.from_session_id and row.from_session is not None:
        return row.from_session.display_pseudonym
    return "someone"


def _open_dialogue_peer_keys(story: Story) -> set[str]:
    """Set of hearer_ref strings that already have an open Dialogue on this Story."""
    from apps.dialogue.models import Dialogue, DialogueStatus

    keys: set[str] = set()
    qs = Dialogue.objects.filter(story=story, status=DialogueStatus.OPEN).only(
        "peer_account_id", "peer_session_id"
    )
    for d in qs:
        if d.peer_account_id:
            keys.add(f"account:{d.peer_account_id}")
        elif d.peer_session_id:
            keys.add(f"session:{d.peer_session_id}")
    return keys


@transaction.atomic
def offer_empathy(actor: Actor, story_id: UUID) -> OfferResult:
    """Idempotent Silent Empathy. Does not expose pulse to non-authors."""
    story = get_story(story_id, for_public=True)
    if story.parent_id:
        raise EmpathyError("Empathy applies to top-level stories only")

    if actor.account is None and actor.session is None:
        raise EmpathyError("Actor has no identity")

    try:
        assert_under_limit(
            actor=actor,
            queryset=SilentEmpathy.objects.all(),
            account_field="from_account",
            session_field="from_session",
            limit=EMPATHY_LIMIT,
            window_seconds=EMPATHY_WINDOW_SECONDS,
        )
    except RateLimitExceeded as exc:
        raise EmpathyError(str(exc)) from exc

    created = False
    row: SilentEmpathy | None = None
    try:
        if actor.account is not None:
            row, created = SilentEmpathy.objects.get_or_create(
                story=story,
                from_account=actor.account,
                defaults={"from_session": None, "outreach_opt_in": True},
            )
        else:
            assert actor.session is not None
            row, created = SilentEmpathy.objects.get_or_create(
                story=story,
                from_session=actor.session,
                defaults={"from_account": None, "outreach_opt_in": True},
            )
    except IntegrityError:
        created = False
        if actor.account is not None:
            row = SilentEmpathy.objects.filter(
                story=story, from_account=actor.account
            ).first()
        else:
            row = SilentEmpathy.objects.filter(
                story=story, from_session=actor.session
            ).first()

    if created:
        pulse, _ = EmpathyPulse.objects.select_for_update().get_or_create(story=story)
        EmpathyPulse.objects.filter(pk=pulse.pk).update(count=F("count") + 1)
        from apps.notifications.models import NotificationKind
        from apps.notifications.services import notify

        if story.author_account_id:
            recipient = Actor(kind="account", account=story.author_account)
        elif story.author_session_id:
            recipient = Actor(kind="anonymous", session=story.author_session)
        else:
            recipient = None
        if recipient is not None:
            notify(
                recipient,
                NotificationKind.SILENT_EMPATHY,
                {"story_id": str(story.id)},
            )

    opt_in = True if row is None else bool(row.outreach_opt_in)
    return OfferResult(created=created, pulse_count=None, outreach_opt_in=opt_in)


def get_pulse_for_author(actor: Actor, story_id: UUID) -> int:
    try:
        story = Story.objects.get(pk=story_id)
    except Story.DoesNotExist as exc:
        raise StoryNotFound("Story not found") from exc
    if not is_author(story, actor):
        raise EmpathyError("Only the author can see Empathy Pulse")
    pulse = ensure_pulse(story)
    return pulse.count


def list_hearers_for_author(actor: Actor, story_id: UUID) -> list[HearerView]:
    """Author-only Hearer List (never public)."""
    try:
        story = Story.objects.get(pk=story_id)
    except Story.DoesNotExist as exc:
        raise StoryNotFound("Story not found") from exc
    if not is_author(story, actor):
        raise EmpathyError("Only the author can see who heard them")

    open_keys = _open_dialogue_peer_keys(story)
    rows = (
        SilentEmpathy.objects.filter(story=story)
        .select_related("from_account", "from_session")
        .order_by("-created_at")
    )
    out: list[HearerView] = []
    for row in rows:
        ref = hearer_ref_for_empathy(row)
        out.append(
            HearerView(
                hearer_ref=ref,
                pseudonym=_pseudonym_for_empathy(row),
                outreach_opt_in=row.outreach_opt_in,
                created_at=row.created_at.isoformat(),
                has_open_dialogue=ref in open_keys,
            )
        )
    return out


@transaction.atomic
def set_outreach_consent(actor: Actor, story_id: UUID, *, opt_in: bool) -> bool:
    """Hearer opt-in/out for Author Outreach on this Story."""
    if actor.account is None and actor.session is None:
        raise EmpathyError("Actor has no identity")

    story = get_story(story_id, for_public=True)
    if actor.account is not None:
        updated = SilentEmpathy.objects.filter(
            story=story, from_account=actor.account
        ).update(outreach_opt_in=opt_in)
    else:
        updated = SilentEmpathy.objects.filter(
            story=story, from_session=actor.session
        ).update(outreach_opt_in=opt_in)

    if not updated:
        raise EmpathyError('Mark "I hear you" first')
    return opt_in


def get_empathy_for_hearer(
    story: Story, hearer: Actor
) -> SilentEmpathy | None:
    if hearer.account is not None:
        return (
            SilentEmpathy.objects.filter(story=story, from_account=hearer.account)
            .select_related("from_account", "from_session")
            .first()
        )
    if hearer.session is not None:
        return (
            SilentEmpathy.objects.filter(story=story, from_session=hearer.session)
            .select_related("from_account", "from_session")
            .first()
        )
    return None


def eligible_hearers_for_outreach(story: Story) -> list[SilentEmpathy]:
    """Opt-in Hearers only (for random / validation)."""
    return list(
        SilentEmpathy.objects.filter(story=story, outreach_opt_in=True)
        .select_related("from_account", "from_session")
        .order_by("-created_at")
    )
