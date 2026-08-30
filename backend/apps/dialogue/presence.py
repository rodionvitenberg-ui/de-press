"""Helper presence: heartbeat window and instant-match pick. No public counts."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from django.db.models import QuerySet
from django.utils import timezone

from apps.fund import services as fund_services
from apps.identity.models import Account
from apps.identity.services import Actor
from apps.moderation.blocks import is_blocked_between

ONLINE_WINDOW = timedelta(seconds=45)


def touch_helper(actor: Actor) -> Account:
    if actor.account is None or not actor.account.is_helper:
        raise PermissionError("Only a Helper can send a heartbeat")
    account = actor.account
    # Duty-fund hook BEFORE refreshing helper_seen_at: it uses the previous
    # heartbeat to detect a long gap and split the stale stretch (ADR-0020).
    fund_services.on_heartbeat(account, prev_seen=account.helper_seen_at)
    account.helper_seen_at = timezone.now()
    account.save(update_fields=["helper_seen_at"])
    return account


def mark_matched(account: Account) -> None:
    account.helper_last_matched_at = timezone.now()
    account.save(update_fields=["helper_last_matched_at"])


def _online_on_duty(*, exclude_id: UUID | None = None) -> QuerySet[Account]:
    cutoff = timezone.now() - ONLINE_WINDOW
    qs = Account.objects.on_duty_helpers().filter(helper_seen_at__gte=cutoff)
    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)
    return qs


def presence_for(actor: Actor) -> dict[str, bool]:
    exclude = actor.account_id
    duty = Account.objects.filter(is_helper=True, is_on_duty=True, is_active=True)
    if exclude is not None:
        duty = duty.exclude(pk=exclude)
    return {
        "someone_on_duty": duty.exists(),
        "someone_online": _online_on_duty(exclude_id=exclude).exists(),
    }


def pick_helper_for_match(requester: Actor) -> Account | None:
    """Least-recently matched on-duty helper with a fresh heartbeat."""
    helpers = sorted(
        _online_on_duty(exclude_id=requester.account_id),
        key=lambda acc: (
            acc.helper_last_matched_at is not None,
            acc.helper_last_matched_at or timezone.now(),
        ),
    )
    for helper in helpers:
        if not is_blocked_between(Actor(kind="account", account=helper), requester):
            return helper
    return None
