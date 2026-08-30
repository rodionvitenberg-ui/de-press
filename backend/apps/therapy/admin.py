from django.contrib import admin

from apps.therapy.models import TherapySession, TherapistProfile
from apps.therapy.services import new_invite_token


@admin.register(TherapistProfile)
class TherapistProfileAdmin(admin.ModelAdmin):
    list_display = ("pseudonym", "account", "is_active", "rate_sol", "claimed_at")
    search_fields = ("pseudonym", "account__email")
    readonly_fields = ("created_at", "claimed_at")
    exclude = ("invite_token",)

    def save_model(self, request, obj, form, change):
        if not change:
            # A fresh profile starts as an unclaimed invite.
            obj.invite_token = new_invite_token()
        super().save_model(request, obj, form, change)


@admin.register(TherapySession)
class TherapySessionAdmin(admin.ModelAdmin):
    list_display = ("id", "therapist", "status", "price_sol", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("therapist", "client_account", "client_session", "dialogue")
    readonly_fields = ("created_at", "updated_at")
