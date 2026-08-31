"""Bug reports: a user sees a problem and files it; staff triages in admin."""

from __future__ import annotations

from apps.common.models import BugReport
from apps.common.rate_limit import RateLimitExceeded, assert_under_limit
from apps.identity.services import Actor

MIN_TEXT = 5
MAX_TEXT = 4000
MAX_PAGE = 200
RATE_LIMIT = 10
RATE_WINDOW_SECONDS = 3600


class BugReportError(Exception):
    pass


def file_bug_report(
    actor: Actor, *, text: str, page: str = "", user_agent: str = ""
) -> BugReport:
    """Validate, rate-limit and store one bug report from the viewer."""
    cleaned = (text or "").strip()
    if len(cleaned) < MIN_TEXT:
        raise BugReportError("Bug description is too short")
    if len(cleaned) > MAX_TEXT:
        raise BugReportError("Bug description is too long")

    try:
        assert_under_limit(
            actor=actor,
            queryset=BugReport.objects.all(),
            account_field="reporter_account",
            session_field="reporter_session",
            limit=RATE_LIMIT,
            window_seconds=RATE_WINDOW_SECONDS,
        )
    except RateLimitExceeded as exc:
        raise BugReportError(str(exc)) from exc

    return BugReport.objects.create(
        reporter_account=actor.account,
        reporter_session=actor.session if actor.account is None else None,
        text=cleaned,
        page=(page or "").strip()[:MAX_PAGE],
        user_agent=(user_agent or "").strip()[:300],
    )
