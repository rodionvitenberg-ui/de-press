"""Block list: one Actor blocks another (for feed + dialogue)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from django.db import IntegrityError, models, transaction
from django.db.models import Q

from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.moderation.models import Block


class BlockError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class BlockResult:
    created: bool


def _identity_pair(actor: Actor) -> tuple[Account | None, AnonymousSession | None]:
    return actor.account, actor.session


@transaction.atomic
def block_actor(blocker: Actor, *, target_account_id: UUID | None = None, target_session_id: UUID | None = None) -> BlockResult:
    if blocker.account is None and blocker.session is None:
        raise BlockError("No identity")
    if (target_account_id is None) == (target_session_id is None):
        raise BlockError("Provide exactly one target")

    if target_account_id and blocker.account and blocker.account.id == target_account_id:
        raise BlockError("Cannot block yourself")
    if target_session_id and blocker.session and blocker.session.id == target_session_id:
        raise BlockError("Cannot block yourself")

    defaults = {
        "blocker_account": blocker.account,
        "blocker_session": blocker.session if blocker.account is None else None,
        "blocked_account_id": target_account_id,
        "blocked_session_id": target_session_id,
    }
    try:
        _, created = Block.objects.get_or_create(
            blocker_account=blocker.account if blocker.account else None,
            blocker_session=blocker.session if blocker.account is None else None,
            blocked_account_id=target_account_id,
            blocked_session_id=target_session_id,
            defaults=defaults,
        )
    except IntegrityError:
        return BlockResult(created=False)
    return BlockResult(created=created)


def has_blocked(blocker: Actor, target: Actor) -> bool:
    """True if blocker has a Block row targeting target (one direction)."""
    q = Q()
    if blocker.account and target.account:
        q |= Q(blocker_account=blocker.account, blocked_account=target.account)
    if blocker.account and target.session:
        q |= Q(blocker_account=blocker.account, blocked_session=target.session)
    if blocker.session and target.account:
        q |= Q(blocker_session=blocker.session, blocked_account=target.account)
    if blocker.session and target.session:
        q |= Q(blocker_session=blocker.session, blocked_session=target.session)
    if not q:
        return False
    return Block.objects.filter(q).exists()


def is_blocked_between(a: Actor, b: Actor) -> bool:
    """True if either side has blocked the other."""
    q = Q()
    # a blocked b
    if a.account and b.account:
        q |= Q(blocker_account=a.account, blocked_account=b.account)
    if a.account and b.session:
        q |= Q(blocker_account=a.account, blocked_session=b.session)
    if a.session and b.account:
        q |= Q(blocker_session=a.session, blocked_account=b.account)
    if a.session and b.session:
        q |= Q(blocker_session=a.session, blocked_session=b.session)
    # b blocked a
    if b.account and a.account:
        q |= Q(blocker_account=b.account, blocked_account=a.account)
    if b.account and a.session:
        q |= Q(blocker_account=b.account, blocked_session=a.session)
    if b.session and a.account:
        q |= Q(blocker_session=b.session, blocked_account=a.account)
    if b.session and a.session:
        q |= Q(blocker_session=b.session, blocked_session=a.session)
    if not q:
        return False
    return Block.objects.filter(q).exists()


def block_peer_in_dialogue(actor: Actor, dialogue_id: UUID) -> BlockResult:
    """Block the other participant of a dialogue (author or peer)."""
    from apps.dialogue.models import Dialogue
    from apps.dialogue.services import DialogueError, get_dialogue_for_participant

    try:
        d = get_dialogue_for_participant(actor, dialogue_id)
    except DialogueError as exc:
        raise BlockError(str(exc)) from exc

    # Determine peer side
    i_am_author = False
    if actor.account and d.author_account_id == actor.account.id:
        i_am_author = True
    if actor.session and d.author_session_id == actor.session.id:
        i_am_author = True

    if i_am_author:
        return block_actor(
            actor,
            target_account_id=d.peer_account_id,
            target_session_id=d.peer_session_id if d.peer_account_id is None else None,
        )
    return block_actor(
        actor,
        target_account_id=d.author_account_id,
        target_session_id=d.author_session_id if d.author_account_id is None else None,
    )


def _peer_target_ids(actor: Actor, dialogue) -> tuple[UUID | None, UUID | None]:
    i_am_author = False
    if actor.account and dialogue.author_account_id == actor.account.id:
        i_am_author = True
    if actor.session and dialogue.author_session_id == actor.session.id:
        i_am_author = True
    if i_am_author:
        acc = dialogue.peer_account_id
        sess = dialogue.peer_session_id if dialogue.peer_account_id is None else None
        return acc, sess
    acc = dialogue.author_account_id
    sess = dialogue.author_session_id if dialogue.author_account_id is None else None
    return acc, sess


def unblock_peer_in_dialogue(actor: Actor, dialogue_id: UUID) -> int:
    """Remove this actor's block of the other participant. Returns rows deleted."""
    from apps.dialogue.services import DialogueError, get_dialogue_for_participant

    try:
        d = get_dialogue_for_participant(actor, dialogue_id)
    except DialogueError as exc:
        raise BlockError(str(exc)) from exc

    acc_id, sess_id = _peer_target_ids(actor, d)
    q = Q()
    if actor.account:
        q &= Q(blocker_account=actor.account)
    elif actor.session:
        q &= Q(blocker_session=actor.session)
    else:
        raise BlockError("No identity")
    if acc_id:
        q &= Q(blocked_account_id=acc_id)
    elif sess_id:
        q &= Q(blocked_session_id=sess_id)
    else:
        return 0
    deleted, _ = Block.objects.filter(q).delete()
    return deleted


def blocked_author_q_for_viewer(viewer: Actor) -> Q:
    """Q object matching Story rows whose author the viewer blocked (or who blocked viewer — hide mutual)."""
    # Stories by people viewer blocked
    blocked = Block.objects.all()
    if viewer.account:
        blocked = blocked.filter(blocker_account=viewer.account)
    elif viewer.session:
        blocked = blocked.filter(blocker_session=viewer.session)
    else:
        return Q(pk__in=[])  # no identity → no blocks

    account_ids = list(
        blocked.exclude(blocked_account_id=None).values_list("blocked_account_id", flat=True)
    )
    session_ids = list(
        blocked.exclude(blocked_session_id=None).values_list("blocked_session_id", flat=True)
    )
    q = Q()
    if account_ids:
        q |= Q(author_account_id__in=account_ids)
    if session_ids:
        q |= Q(author_session_id__in=session_ids)
    return q if q else Q(pk__in=[])


def blocked_author_keys_for(viewer: Actor) -> set[str]:
    """Opaque author_key values the viewer should not see on the live feed."""
    if viewer.account is None and viewer.session is None:
        return set()
    blocked = Block.objects.all()
    if viewer.account:
        blocked = blocked.filter(blocker_account=viewer.account)
    elif viewer.session:
        blocked = blocked.filter(blocker_session=viewer.session)
    keys: set[str] = set()
    for acc_id in blocked.exclude(blocked_account_id=None).values_list(
        "blocked_account_id", flat=True
    ):
        keys.add(f"a:{acc_id}")
    for sess_id in blocked.exclude(blocked_session_id=None).values_list(
        "blocked_session_id", flat=True
    ):
        keys.add(f"s:{sess_id}")
    return keys
