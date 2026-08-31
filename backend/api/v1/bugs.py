"""Bug reports from the UI (More → Report a bug)."""

from __future__ import annotations

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.common.bugs import BugReportError, file_bug_report
from apps.identity.services import require_actor

router = Router(tags=["bugs"])


class BugIn(Schema):
    text: str
    page: str = ""


class BugOut(Schema):
    ok: bool
    id: str


@router.post("/bugs", response=BugOut)
def report_bug(request, payload: BugIn):
    """File a bug report; identity attaches automatically, no login required."""
    actor = require_actor(request)
    try:
        bug = file_bug_report(
            actor,
            text=payload.text,
            page=payload.page,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    except BugReportError as exc:
        raise HttpError(400, str(exc))
    return BugOut(ok=True, id=str(bug.id))
