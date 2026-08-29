from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.identity.models import Account, AnonymousSession, HelperInvite


@admin.register(Account)
class AccountAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "default_pseudonym",
        "is_helper",
        "helper_org",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_helper", "is_staff", "is_active")
    search_fields = ("email", "default_pseudonym", "helper_org")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("default_pseudonym",)}),
        ("Helper", {"fields": ("is_helper", "helper_org")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(HelperInvite)
class HelperInviteAdmin(admin.ModelAdmin):
    list_display = ("token", "org", "created_by", "expires_at", "used_at", "used_by")
    search_fields = ("token", "org")
    raw_id_fields = ("created_by", "used_by")
    readonly_fields = ("id", "token", "created_at", "used_at")


@admin.register(AnonymousSession)
class AnonymousSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "pseudonym", "created_at", "last_seen_at")
    search_fields = ("id", "pseudonym")
    readonly_fields = ("id", "created_at", "last_seen_at")
