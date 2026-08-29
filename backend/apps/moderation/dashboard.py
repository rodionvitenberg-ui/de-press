"""Helper dashboard: этичные ops-метрики для модерации (не public metrics).

Сводка очередей и недавняя активность репортов. Никаких «public vanity metrics»:
только внутренние агрегаты для команды/хелперов.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from apps.moderation.models import Report
from apps.support.models import SupportCloud, SupportCloudStatus


@dataclass(frozen=True, slots=True)
class ReportRowView:
    id: str
    reason: str
    status: str
    story_preview: str
    details: str
    created_at: str


@dataclass(frozen=True, slots=True)
class DashboardView:
    pending_clouds: int
    open_reports: int
    reviewing_reports: int
    reports_last_7d: int
    recent_reports: list[ReportRowView]


def build_dashboard() -> DashboardView:
    """Лёгкая сводка для страницы хелпера (без тяжёлых агрегатов)."""
    pending_clouds = SupportCloud.objects.filter(
        status=SupportCloudStatus.PENDING
    ).count()
    open_reports = Report.objects.filter(status="open").count()
    reviewing_reports = Report.objects.filter(status="reviewing").count()

    since = timezone.now() - timezone.timedelta(days=7)
    reports_last_7d = Report.objects.filter(created_at__gte=since).count()

    recent_rows = Report.objects.order_by("-created_at").select_related(
        "story", "message"
    )[:10]
    recent = []
    for r in recent_rows:
        if r.story_id and r.story is not None:
            preview = (r.story.body or "")[:120]
        elif r.message_id and r.message is not None:
            preview = (r.message.body or "")[:120]
        else:
            preview = ""
        recent.append(
            ReportRowView(
                id=str(r.id),
                reason=r.reason,
                status=r.status,
                story_preview=preview,
                details=(r.details or "")[:200],
                created_at=r.created_at.isoformat(),
            )
        )
    return DashboardView(
        pending_clouds=pending_clouds,
        open_reports=open_reports,
        reviewing_reports=reviewing_reports,
        reports_last_7d=reports_last_7d,
        recent_reports=recent,
    )