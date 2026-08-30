"""Therapy endpoints (ADR 0022): statuses and references only.

No payment processing, no keys, no balances. The client pays the therapist
directly (Solana Pay); confirmation is manual by the therapist.
"""

from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.identity.services import resolve_actor
from apps.therapy.models import TherapySession, TherapistProfile
from apps.therapy.services import (
    TherapyError,
    claim_invite,
    client_label,
    client_sessions,
    complete_session,
    confirm_payment,
    create_session,
    decline_session,
    get_active_profiles,
    get_session_for_participant,
    mark_i_paid,
    therapist_sessions,
)

router = Router(tags=["therapy"])


class TherapistOut(Schema):
    id: str
    pseudonym: str
    approach: str
    languages: str
    rate_sol: float
    solana_address: str


@router.get("/therapy/profiles", response=list[TherapistOut])
def therapist_profiles(request):
    """Public catalog: active therapists with their Solana payment address."""
    return [
        TherapistOut(
            id=str(p.id),
            pseudonym=p.pseudonym,
            approach=p.approach,
            languages=p.languages,
            rate_sol=float(p.rate_sol),
            solana_address=p.solana_address,
        )
        for p in get_active_profiles()
    ]


class ClaimIn(Schema):
    token: str


@router.post("/therapy/claim", response=TherapistOut)
def therapy_claim(request, payload: ClaimIn):
    actor = resolve_actor(request)
    try:
        p = claim_invite(actor, payload.token)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return TherapistOut(
        id=str(p.id),
        pseudonym=p.pseudonym,
        approach=p.approach,
        languages=p.languages,
        rate_sol=float(p.rate_sol),
        solana_address=p.solana_address,
    )


class SessionCreateIn(Schema):
    therapist_id: str
    note: str = ""


class SessionOut(Schema):
    id: str
    therapist_id: str
    therapist_label: str
    client_label: str
    status: str
    price_sol: float
    note: str
    solana_address: str
    dialogue_id: str | None = None
    created_at: str
    updated_at: str


def _session_out(st: TherapySession) -> SessionOut:
    return SessionOut(
        id=str(st.id),
        therapist_id=str(st.therapist_id),
        therapist_label=st.therapist.pseudonym,
        client_label=client_label(st),
        status=st.status,
        price_sol=float(st.price_sol),
        note=st.note,
        solana_address=st.therapist.solana_address,
        dialogue_id=str(st.dialogue_id) if st.dialogue_id else None,
        created_at=st.created_at.isoformat(),
        updated_at=st.updated_at.isoformat(),
    )


@router.post("/therapy/sessions", response=SessionOut)
def create_therapy_session(request, payload: SessionCreateIn):
    actor = resolve_actor(request)
    try:
        st = create_session(actor, payload.therapist_id, payload.note)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return _session_out(st)


@router.get("/me/therapy/sessions", response=list[SessionOut])
def my_therapy_sessions(request):
    actor = resolve_actor(request)
    return [_session_out(st) for st in client_sessions(actor)]


@router.get("/me/therapy/inbox", response=list[SessionOut])
def therapy_inbox(request):
    actor = resolve_actor(request)
    return [_session_out(st) for st in therapist_sessions(actor)]


@router.post("/therapy/sessions/{sid}/i-paid", response=SessionOut)
def session_i_paid(request, sid: str):
    actor = resolve_actor(request)
    try:
        st = mark_i_paid(actor, sid)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return _session_out(st)


@router.post("/therapy/sessions/{sid}/confirm", response=SessionOut)
def session_confirm(request, sid: str):
    actor = resolve_actor(request)
    try:
        st = confirm_payment(actor, sid)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return _session_out(st)


@router.post("/therapy/sessions/{sid}/decline", response=SessionOut)
def session_decline(request, sid: str):
    actor = resolve_actor(request)
    try:
        st = decline_session(actor, sid)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return _session_out(st)


@router.post("/therapy/sessions/{sid}/complete", response=SessionOut)
def session_complete(request, sid: str):
    actor = resolve_actor(request)
    try:
        st = complete_session(actor, sid)
    except TherapyError as exc:
        raise HttpError(400, str(exc)) from exc
    return _session_out(st)


@router.get("/therapy/sessions/{sid}", response=SessionOut)
def therapy_session_detail(request, sid: str):
    actor = resolve_actor(request)
    try:
        st = get_session_for_participant(actor, sid)
    except TherapyError as exc:
        raise HttpError(404, str(exc)) from exc
    return _session_out(st)
