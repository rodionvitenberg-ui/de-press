from django.contrib import admin, messages
from django.utils import timezone

from apps.support.models import QuietPhrase, SupportCloud, SupportCloudStatus


@admin.register(QuietPhrase)
class QuietPhraseAdmin(admin.ModelAdmin):
    list_display = ("key", "text_ru", "text_en", "sort_order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("key", "text_ru", "text_en")
    ordering = ("sort_order", "key")


@admin.action(description="Approve selected Moderated Clouds")
def approve_clouds(modeladmin, request, queryset):
    n = 0
    for cloud in queryset.filter(status=SupportCloudStatus.PENDING):
        cloud.status = SupportCloudStatus.DELIVERED
        cloud.moderated_at = timezone.now()
        cloud.moderated_by = request.user if request.user.is_authenticated else None
        cloud.save(update_fields=["status", "moderated_at", "moderated_by"])
        n += 1
    modeladmin.message_user(request, f"Approved {n} cloud(s).", messages.SUCCESS)


@admin.action(description="Reject selected Moderated Clouds")
def reject_clouds(modeladmin, request, queryset):
    n = 0
    for cloud in queryset.filter(status=SupportCloudStatus.PENDING):
        cloud.status = SupportCloudStatus.REJECTED
        cloud.moderated_at = timezone.now()
        cloud.moderated_by = request.user if request.user.is_authenticated else None
        cloud.save(update_fields=["status", "moderated_at", "moderated_by"])
        n += 1
    modeladmin.message_user(request, f"Rejected {n} cloud(s).", messages.WARNING)


@admin.register(SupportCloud)
class SupportCloudAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "story",
        "kind",
        "status",
        "is_priority",
        "helper_badge",
        "pseudonym_snapshot",
        "body_snapshot",
        "created_at",
        "moderated_at",
    )
    list_filter = ("kind", "status", "is_priority")
    search_fields = ("body_snapshot", "pseudonym_snapshot", "helper_badge")
    actions = (approve_clouds, reject_clouds)
    readonly_fields = (
        "id",
        "story",
        "from_account",
        "from_session",
        "kind",
        "phrase",
        "body_snapshot",
        "pseudonym_snapshot",
        "helper_badge",
        "is_priority",
        "created_at",
        "moderated_at",
        "moderated_by",
    )
    raw_id_fields = (
        "story",
        "from_account",
        "from_session",
        "phrase",
        "moderated_by",
    )

    def has_add_permission(self, request):
        return False
