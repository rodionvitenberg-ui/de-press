"""Therapy contour services (ADR 0022): statuses only, no money handling."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from apps.dialogue.models import Dialogue, DialogueSource, DialogueStatus
from apps.identity.services import Actor
from apps.therapy.models import (
    TherapySession,
    TherapySessionStatus,
    TherapistProfile,
)

if TYPE_CHECKING:
    from apps.identity.models import Account, AnonymousSession

OPEN_STATUSES = (
    TherapySessionStatus.AWAITING_PAYMENT,
    TherapySessionStatus.PAYMENT_CLAIMED,
    TherapySessionStatus.PAID,
)


class TherapyError(Exception):
    """User-facing error message; the API layer raises HTTP 400 from it."""


def new_invite_token() -> str:
    return secrets.token_urlsafe(24)


def get_active_profiles() -> list[TherapistProfile]:
    return list(
        TherapistProfile.objects.filter(is_active=True, account__isnull=False)
        .exclude(solana_address="")
        .order_by("pseudonym")
    )


def claim_invite(actor: Actor, token: str) -> TherapistProfile:
    """Bind an admin-created profile to the claiming account."""
    if actor.account is None:
        raise TherapyError("Only an account can claim an invite, not an anonymous session")
    try:
        profile = TherapistProfile.objects.select_for_update().get(
            invite_token=(token or "").strip()
        )
    except TherapistProfile.DoesNotExist:
        raise TherapyError("Invite not found") from None
    if profile.account is not None:
        raise TherapyError("Invite already claimed")
    profile.account = actor.account
    profile.is_active = True
    profile.claimed_at = timezone.now()
    profile.save(update_fields=["account", "is_active", "claimed_at"])
    return profile


def _client_of(actor: Actor) -> tuple["Account | None", "AnonymousSession | None"]:
    if actor.account is not None:
        return actor.account, None
    if actor.session is not None:
        return None, actor.session
    raise TherapyError("Unknown client")


def create_session(actor: Actor, therapist_id: str, note: str = "") -> TherapySession:
    try:
        profile = TherapistProfile.objects.get(pk=therapist_id)
    except (ValueError, TypeError, TherapistProfile.DoesNotExist):
        raise TherapyError("Therapist not found") from None
    if not profile.is_active or profile.account is None:
        raise TherapyError("Therapist is currently unavailable")
    if not (profile.solana_address or "").strip():
        raise TherapyError("Therapist has no payout address yet")
    account, session = _client_of(actor)
    if account is not None and account.id == profile.account_id:
        raise TherapyError("You cannot request a session with yourself")
    duplicate = TherapySession.objects.filter(
        therapist=profile,
        client_account=account,
        client_session=session,
        status__in=OPEN_STATUSES,
    ).exists()
    if duplicate:
        raise TherapyError("You already have an active session with this therapist")
    return TherapySession.objects.create(
        therapist=profile,
        client_account=account,
        client_session=session,
        note=(note or "").strip()[:280],
        price_sol=profile.rate_sol,
    )


def get_session_for_participant(actor: Actor, session_id: str) -> TherapySession:
    try:
        st = TherapySession.objects.select_related(
            "therapist", "therapist__account", "client_account", "client_session"
        ).get(pk=session_id)
    except (ValueError, TypeError, TherapySession.DoesNotExist):
        raise TherapyError("Session not found") from None
    mine_client = (
        (actor.account is not None and st.client_account_id == actor.account.id)
        or (actor.session is not None and st.client_session_id == actor.session.id)
    )
    mine_therapist = (
        actor.account is not None and st.therapist.account_id == actor.account.id
    )
    if not (mine_client or mine_therapist):
        raise TherapyError("Session not found")
    return st


def mark_i_paid(actor: Actor, session_id: str) -> TherapySession:
    st = get_session_for_participant(actor, session_id)
    mine_client = (
        (actor.account is not None and st.client_account_id == actor.account.id)
        or (actor.session is not None and st.client_session_id == actor.session.id)
    )
    if not mine_client:
        raise TherapyError("Only the client can mark payment")
    if st.status != TherapySessionStatus.AWAITING_PAYMENT:
        raise TherapyError("Session is no longer awaiting payment")
    st.status = TherapySessionStatus.PAYMENT_CLAIMED
    st.save(update_fields=["status", "updated_at"])
    return st


def _therapist_session(actor: Actor, session_id: str) -> TherapySession:
    st = get_session_for_participant(actor, session_id)
    if actor.account is None or st.therapist.account_id != actor.account.id:
        raise TherapyError("Only the therapist can perform this action")
    return st


@transaction.atomic
def confirm_payment(actor: Actor, session_id: str) -> TherapySession:
    """Therapist manually confirms the transfer → paid + 1:1 dialogue."""
    st = _therapist_session(actor, session_id)
    st = TherapySession.objects.select_for_update().get(pk=st.pk)
    if st.status != TherapySessionStatus.PAYMENT_CLAIMED:
        if st.status == TherapySessionStatus.PAID:
            return st  # idempotent re-confirm
        raise TherapyError("The client has not marked payment yet")
    if st.dialogue_id is None:
        st.dialogue = Dialogue.objects.create(
            author_account=st.therapist.account,
            peer_account=st.client_account,
            peer_session=st.client_session,
            source=DialogueSource.THERAPY,
            status=DialogueStatus.OPEN,
        )
    st.status = TherapySessionStatus.PAID
    st.save(update_fields=["status", "dialogue", "updated_at"])
    return st


def decline_session(actor: Actor, session_id: str) -> TherapySession:
    st = _therapist_session(actor, session_id)
    if st.status not in (
        TherapySessionStatus.AWAITING_PAYMENT,
        TherapySessionStatus.PAYMENT_CLAIMED,
    ):
        raise TherapyError("This session cannot be declined")
    st.status = TherapySessionStatus.DECLINED
    st.save(update_fields=["status", "updated_at"])
    return st


def complete_session(actor: Actor, session_id: str) -> TherapySession:
    st = _therapist_session(actor, session_id)
    if st.status != TherapySessionStatus.PAID:
        raise TherapyError("Only a paid session can be completed")
    st.status = TherapySessionStatus.DONE
    st.save(update_fields=["status", "updated_at"])
    return st


def client_sessions(actor: Actor) -> list[TherapySession]:
    if actor.account is None and actor.session is None:
        return []  # fully anonymous visitor: nothing to list, no error
    account, session = _client_of(actor)
    qs = TherapySession.objects.select_related(
        "therapist", "therapist__account", "client_account", "client_session"
    )
    if account is not None:
        return list(qs.filter(client_account=account))
    return list(qs.filter(client_session=session))


def therapist_sessions(actor: Actor) -> list[TherapySession]:
    if actor.account is None:
        return []
    return list(
        TherapySession.objects.filter(therapist__account=actor.account)
        .select_related(
            "therapist", "therapist__account", "client_account", "client_session"
        )
    )


def client_label(st: TherapySession) -> str:
    """Pseudonymous client label for the therapist dashboard."""
    if st.client_account_id is not None:
        acc = st.client_account
        if acc is not None and (acc.display_pseudonym or "").strip():
            return acc.display_pseudonym
    if st.client_session_id is not None:
        sess = st.client_session
        if sess is not None and (sess.pseudonym or "").strip():
            return sess.pseudonym
    return "client"
