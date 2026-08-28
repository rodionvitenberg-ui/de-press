from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "kind",
        "recipient_account",
        "recipient_session",
        "is_read",
        "created_at",
    )
    list_filter = ("kind", "is_read")
    search_fields = ("id",)
    date_hierarchy = "created_at"
    readonly_fields = (
        "id",
        "recipient_account",
        "recipient_session",
        "kind",
        "payload",
        "is_read",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False