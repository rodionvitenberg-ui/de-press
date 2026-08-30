from django.contrib import admin

from .models import DutySegment


@admin.register(DutySegment)
class DutySegmentAdmin(admin.ModelAdmin):
    list_display = ("helper", "started_at", "ended_at", "close_reason")
    list_filter = ("close_reason",)
    search_fields = ("helper__email",)
    readonly_fields = ("created_at",)