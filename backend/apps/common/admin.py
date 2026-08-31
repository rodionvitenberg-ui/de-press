from django.contrib import admin

from apps.common.models import BugReport


class ReadOnlyAdmin(admin.ModelAdmin):
    """View-only admin base — rows are written by services, not by staff."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    """Bug inbox: rows come from the /bugs API; staff only triages status."""

    list_display = ("created_at", "status", "reporter_label", "short_text")
    list_editable = ("status",)
    list_filter = ("status",)
    date_hierarchy = "created_at"
    search_fields = ("text", "page")
    readonly_fields = (
        "id",
        "text",
        "page",
        "user_agent",
        "reporter_account",
        "reporter_session",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Reporter")
    def reporter_label(self, obj: BugReport) -> str:
        if obj.reporter_account_id:
            return obj.reporter_account.display_pseudonym
        if obj.reporter_session_id:
            return obj.reporter_session.display_pseudonym
        return "—"

    @admin.display(description="Bug")
    def short_text(self, obj: BugReport) -> str:
        return obj.text[:100]

    def has_add_permission(self, request):
        return False
