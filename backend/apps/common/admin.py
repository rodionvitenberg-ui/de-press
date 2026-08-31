from django.contrib import admin


class ReadOnlyAdmin(admin.ModelAdmin):
    """View-only admin base — rows are written by services, not by staff."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
