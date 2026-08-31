from django.contrib import admin

from apps.common.admin import ReadOnlyAdmin
from apps.notifications.models import EmailDigest, Notification


@admin.register(Notification)
class NotificationAdmin(ReadOnlyAdmin):
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


@admin.register(EmailDigest)
class EmailDigestAdmin(ReadOnlyAdmin):
    """Outbound soft-notify digests — view only, rows are written by services."""

    list_display = (
        "id",
        "to_email",
        "subject",
        "status",
        "recipient_account",
        "recipient_session",
        "created_at",
        "sent_at",
    )
    list_filter = ("status",)
    search_fields = ("id", "to_email", "subject")
    date_hierarchy = "created_at"
    readonly_fields = (
        "id",
        "recipient_account",
        "recipient_session",
        "to_email",
        "token",
        "subject",
        "body_text",
        "payload",
        "status",
        "created_at",
        "sent_at",
        "failed_reason",
    )