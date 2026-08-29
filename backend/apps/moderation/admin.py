from django.contrib import admin, messages

from apps.moderation.models import Block, Report, ReportStatus
from apps.moderation.services import resolve_report
from apps.stories.models import StoryStatus
from apps.stories.services import moderate_story


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
            resolve_report(report.id, status=ReportStatus.REVIEWING)
        self.message_user(request, "Marked reviewing.", messages.SUCCESS)

    @admin.action(description="Dismiss selected reports")
    def dismiss_reports(self, request, queryset):
        for report in queryset:
            resolve_report(report.id, status=ReportStatus.RESOLVED_DISMISSED)
        self.message_user(request, "Dismissed.", messages.SUCCESS)

    @admin.action(description="Hide story and resolve reports")
    def hide_story_and_resolve(self, request, queryset):
        story_ids = set()
        for report in queryset:
            resolve_report(
                report.id,
                status=ReportStatus.RESOLVED_HIDDEN,
                hide_story=True,
            )
            if report.story_id:
                story_ids.add(report.story_id)
                Report.objects.filter(
                    story_id=report.story_id,
                    status=ReportStatus.OPEN,
                ).exclude(pk=report.pk).update(status=ReportStatus.RESOLVED_HIDDEN)
        for sid in story_ids:
            if sid:
                moderate_story(sid, StoryStatus.HIDDEN)
        self.message_user(
            request,
            f"Hidden {len(story_ids)} stor(ies) and resolved reports.",
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
