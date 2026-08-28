from django.contrib import admin

from apps.empathy.models import EmpathyPulse, SilentEmpathy


@admin.register(SilentEmpathy)
class SilentEmpathyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "story",
        "from_account",
        "from_session",
        "outreach_opt_in",
        "created_at",
    )
    list_filter = ("outreach_opt_in",)
    readonly_fields = ("id", "created_at")
    raw_id_fields = ("story", "from_account", "from_session")


@admin.register(EmpathyPulse)
class EmpathyPulseAdmin(admin.ModelAdmin):
    list_display = ("story", "count", "updated_at")
    readonly_fields = ("story", "count", "updated_at")

    def has_add_permission(self, request):
        return False
