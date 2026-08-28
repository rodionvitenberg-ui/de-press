from django.contrib import admin

from apps.stories.models import Story


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "topic",
        "status",
        "pseudonym_snapshot",
        "author_account",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "topic")
    search_fields = ("body", "pseudonym_snapshot", "id")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("author_account", "author_session")
    actions = ("hide_stories", "remove_stories", "publish_stories")

    @admin.action(description="Hide selected stories")
    def hide_stories(self, request, queryset):
        queryset.update(status="hidden")

    @admin.action(description="Remove selected stories")
    def remove_stories(self, request, queryset):
        queryset.update(status="removed")

    @admin.action(description="Publish selected stories")
    def publish_stories(self, request, queryset):
        queryset.update(status="published")
