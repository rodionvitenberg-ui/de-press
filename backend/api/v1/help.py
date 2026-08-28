"""Help Request HTTP API: visitor asks; Helper inbox / accept / skip."""

from __future__ import annotations

from uuid import UUID

from ninja import Router, Schema
from ninja.errors import HttpError

from api.v1.dialogue import DialogueOut, _dialogue_out
from apps.dialogue.help import (
    HelpError,
    accept_help_request,
    cancel_help_request,
    create_help_request,
    list_help_inbox,
    my_help_request,
    skip_help_request,
)
from apps.identity.services import require_actor

router = Router(tags=["help"])


class HelpIn(Schema):
    note: str = ""


class HelpOut(Schema):
    id: str
    note: str
    status: str
    dialogue_id: str | None = None
    created_at: str


def _help_out(req) -> HelpOut:
    return HelpOut(
        id=str(req.id),
        note=req.note or "",
        status=req.status,
        dialogue_id=str(req.dialogue_id) if req.dialogue_id else None,
        created_at=req.created_at.isoformat(),
    )


def _raise_help(exc: HelpError) -> None:
    msg = str(exc)
    if "not found" in msg.lower():
        raise HttpError(404, msg) from exc
    if "Helper" in msg:
        raise HttpError(403, msg) from exc
    raise HttpError(400, msg) from exc


def _require_helper(actor) -> None:
    if actor.account is None or not actor.account.is_helper:
        raise HttpError(403, "Only a Helper can access help inbox")


@router.post("/help/requests", response=HelpOut)
def post_help_request(request, payload: HelpIn):
    actor = require_actor(request)
    try:
        req = create_help_request(actor, note=payload.note)
    except HelpError as exc:
        _raise_help(exc)
    return _help_out(req)


@router.get("/help/requests/mine", response=HelpOut)
def get_my_help_request(request):
    actor = require_actor(request)
    req = my_help_request(actor)
    if req is None:
        raise HttpError(404, "No help request")
    return _help_out(req)


@router.get("/help/requests", response=list[HelpOut])
def get_help_inbox(request):
    actor = require_actor(request)
    _require_helper(actor)
    return [_help_out(r) for r in list_help_inbox(actor)]


@router.post("/help/requests/{request_id}/accept", response=DialogueOut)
def post_accept_help(request, request_id: UUID):
    actor = require_actor(request)
    try:
        dialogue = accept_help_request(actor, request_id)
    except HelpError as exc:
        _raise_help(exc)
    return _dialogue_out(dialogue, actor)


@router.post("/help/requests/{request_id}/skip", response=HelpOut)
def post_skip_help(request, request_id: UUID):
    actor = require_actor(request)
    try:
        req = skip_help_request(actor, request_id)
    except HelpError as exc:
        _raise_help(exc)
    return _help_out(req)


@router.post("/help/requests/{request_id}/cancel", response=HelpOut)
def post_cancel_help(request, request_id: UUID):
    actor = require_actor(request)
    try:
        req = cancel_help_request(actor, request_id)
    except HelpError as exc:
        _raise_help(exc)
    return _help_out(req)
