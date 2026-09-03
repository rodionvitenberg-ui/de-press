"""Simple time-window rate limits keyed by Actor."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.identity.services import Actor


class RateLimitExceeded(Exception):
    def __init__(self, message: str = "Too many actions. Please wait a bit."):
        super().__init__(message)


def _actor_filters(actor: Actor, account_field: str, session_field: str) -> dict:
    if actor.account is not None:
        return {account_field: actor.account}
    if actor.session is not None:
        return {session_field: actor.session}
    raise RateLimitExceeded("No identity for rate limit")


def assert_under_limit(
    *,
    actor: Actor,
    queryset,
    account_field: str,
    session_field: str,
    limit: int,
    window_seconds: int,
    time_field: str = "created_at",
) -> None:
    """Raise RateLimitExceeded if actor has >= limit rows in the time window."""
    since = timezone.now() - timedelta(seconds=window_seconds)
    filters = _actor_filters(actor, account_field, session_field)
    filters[f"{time_field}__gte"] = since
    count = queryset.filter(**filters).count()
    if count >= limit:
        raise RateLimitExceeded()
