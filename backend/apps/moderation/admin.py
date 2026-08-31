from django.contrib import admin, messages

from apps.common.admin import ReadOnlyAdmin
from apps.moderation.models import (
    Block,
    ModerationAction,
    Report,
    ReportReason,
    ReportStatus,
)
from apps.moderation.services import resolve_report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "story",
        "message",
        "reason",
        "status",
        "from_account",
        "from_session",
        "created_at",
        "open_count_hint",
    )
    list_filter = ("status", "reason", "created_at")
    search_fields = ("id", "details", "story__id", "story__body")
    raw_id_fields = ("story", "message", "from_account", "from_session")
    readonly_fields = ("id", "created_at", "updated_at")
    actions = (
        "mark_reviewing",
        "dismiss_reports",
        "hide_story_and_resolve",
    )

    @admin.display(description="Open reports on story")
    def open_count_hint(self, obj: Report) -> int:
        if obj.story_id:
            return Report.objects.filter(
                story_id=obj.story_id,
                status=ReportStatus.OPEN,
            ).count()
        if obj.message_id:
            return Report.objects.filter(
                message_id=obj.message_id,
                status=ReportStatus.OPEN,
            ).count()
        return 0

    @admin.action(description="Mark as reviewing")
    def mark_reviewing(self, request, queryset):
        for report in queryset:
            resolve_report(report.id, actor=request.user, decision="reviewing")
        self.message_user(request, "Marked reviewing.", messages.SUCCESS)

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        for report in queryset:
            resolve_report(
                report.id,
                actor=request.user,
                decision="dismiss",
                reason=ReportReason.OTHER,
                note="Dismissed via Django admin",
            )
        self.message_user(request, "Dismissed.", messages.SUCCESS)

    @admin.action(description="Hide content and resolve reports")
    def hide_story_and_resolve(self, request, queryset):
        for report in queryset:
            resolve_report(
                report.id,
                actor=request.user,
                decision="hide",
                reason=ReportReason.OTHER,
                note="Hidden via Django admin",
            )
        self.message_user(
            request,
            "Content hidden and reports resolved.",
            messages.SUCCESS,
        )


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "blocker_account",
        "blocker_session",
        "blocked_account",
        "blocked_session",
        "created_at",
    )
    raw_id_fields = (
        "blocker_account",
        "blocker_session",
        "blocked_account",
        "blocked_session",
    )
    readonly_fields = ("id", "created_at")


@admin.register(ModerationAction)
class ModerationActionAdmin(ReadOnlyAdmin):
    """Audit log (Q12) — view only, rows are written by resolve_report."""

    list_display = (
        "id",
        "action",
        "reason",
        "story",
        "message",
        "report",
        "actor",
        "created_at",
    )
    list_filter = ("action", "reason")
    date_hierarchy = "created_at"
    readonly_fields = (
        "id",
        "report",
        "story",
        "message",
        "actor",
        "action",
        "reason",
        "note",
        "created_at",
    )
