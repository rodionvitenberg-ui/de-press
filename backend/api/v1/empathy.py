from __future__ import annotations

from uuid import UUID

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.empathy.services import (
    EmpathyError,
    get_pulse_for_author,
    list_hearers_for_author,
    offer_empathy,
    set_outreach_consent,
)
from apps.identity.services import require_actor
from apps.stories.services import StoryNotFound

router = Router(tags=["empathy"])


class EmpathyOut(Schema):
    ok: bool
    created: bool
    message: str
    outreach_opt_in: bool = True


class PulseOut(Schema):
    story_id: str
    count: int
    message: str


class HearerOut(Schema):
    hearer_ref: str
    pseudonym: str
    outreach_opt_in: bool
    created_at: str
    has_open_dialogue: bool


class OutreachConsentIn(Schema):
    outreach_opt_in: bool


class OutreachConsentOut(Schema):
    ok: bool
    outreach_opt_in: bool
    message: str


@router.post("/stories/{story_id}/empathy", response=EmpathyOut)
def post_empathy(request, story_id: UUID):
    actor = require_actor(request)
    try:
        result = offer_empathy(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except EmpathyError as exc:
        raise HttpError(400, str(exc)) from exc
    return EmpathyOut(
        ok=True,
        created=result.created,
        message="Я слышу тебя" if result.created else "Уже отмечено",
        outreach_opt_in=result.outreach_opt_in,
    )


@router.get("/stories/{story_id}/pulse", response=PulseOut)
def get_pulse(request, story_id: UUID):
    actor = require_actor(request)
    try:
        count = get_pulse_for_author(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except EmpathyError as exc:
        raise HttpError(403, str(exc)) from exc
    return PulseOut(
        story_id=str(story_id),
        count=count,
        message=f"{count} человек прочитали и посидели с тобой молча."
        if count
        else "Пока тихо. Это тоже нормально.",
    )


@router.get("/stories/{story_id}/hearers", response=list[HearerOut])
def get_hearers(request, story_id: UUID):
    actor = require_actor(request)
    try:
        hearers = list_hearers_for_author(actor, story_id)
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except EmpathyError as exc:
        raise HttpError(403, str(exc)) from exc
    return [
        HearerOut(
            hearer_ref=h.hearer_ref,
            pseudonym=h.pseudonym,
            outreach_opt_in=h.outreach_opt_in,
            created_at=h.created_at,
            has_open_dialogue=h.has_open_dialogue,
        )
        for h in hearers
    ]


@router.post(
    "/stories/{story_id}/empathy/outreach-consent",
    response=OutreachConsentOut,
)
def post_outreach_consent(request, story_id: UUID, payload: OutreachConsentIn):
    actor = require_actor(request)
    try:
        opt_in = set_outreach_consent(
            actor, story_id, opt_in=payload.outreach_opt_in
        )
    except StoryNotFound as exc:
        raise HttpError(404, str(exc)) from exc
    except EmpathyError as exc:
        raise HttpError(400, str(exc)) from exc
    if opt_in:
        msg = "Автор сможет написать тебе, если отметишь «Я слышу тебя»."
    else:
        msg = "Автор не сможет написать тебе через outreach по этой истории."
    return OutreachConsentOut(ok=True, outreach_opt_in=opt_in, message=msg)
