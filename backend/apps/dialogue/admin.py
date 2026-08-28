from django.contrib import admin

from apps.dialogue.models import Dialogue, DialogueRequest, Message


@admin.register(DialogueRequest)
class DialogueRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "story", "intent", "status", "from_account", "created_at")
    list_filter = ("status", "intent")
    raw_id_fields = ("story", "from_account", "from_session")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Dialogue)
class DialogueAdmin(admin.ModelAdmin):
    list_display = ("id", "story", "intent", "status", "created_at", "updated_at")
    list_filter = ("status", "intent")
    raw_id_fields = (
        "story",
        "request",
        "author_account",
        "author_session",
        "peer_account",
        "peer_session",
    )
    readonly_fields = ("id", "created_at", "updated_at", "closed_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "dialogue", "kind", "ephemeral", "source_lang", "created_at")
    list_filter = ("kind", "ephemeral")
    raw_id_fields = ("dialogue", "from_account", "from_session")
    readonly_fields = ("id", "created_at", "transcript", "translations")
