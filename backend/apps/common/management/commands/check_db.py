"""Print which database Django is using and key row counts."""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Show active DB binding and Story/Dialogue counts (local diagnostics)"

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "")
        self.stdout.write(f"ENGINE={engine}")
        self.stdout.write(f"NAME={db.get('NAME')}")
        self.stdout.write(f"HOST={db.get('HOST', '')}")
        self.stdout.write(f"PORT={db.get('PORT', '')}")
        self.stdout.write(f"USER={db.get('USER', '')}")

        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS("connection=ok"))
        except Exception as exc:  # noqa: BLE001 — diagnostic command
            self.stdout.write(self.style.ERROR(f"connection=FAIL: {exc}"))
            return

        from apps.dialogue.models import Dialogue, DialogueRequest, Message
        from apps.identity.models import Account, AnonymousSession
        from apps.stories.models import Story

        self.stdout.write(f"stories={Story.objects.count()}")
        self.stdout.write(
            f"stories_published={Story.objects.filter(status='published').count()}"
        )
        self.stdout.write(f"dialogues={Dialogue.objects.count()}")
        self.stdout.write(f"dialogue_requests={DialogueRequest.objects.count()}")
        self.stdout.write(f"messages={Message.objects.count()}")
        self.stdout.write(f"accounts={Account.objects.count()}")
        self.stdout.write(f"anonymous_sessions={AnonymousSession.objects.count()}")

        if "sqlite" in engine:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: SQLite is active. Local product data lives in Postgres "
                    "database 'depress' — you will not see that data here."
                )
            )
        elif db.get("NAME") != "depress":
            self.stdout.write(
                self.style.WARNING(
                    f"WARNING: expected database name 'depress', got {db.get('NAME')!r}."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("bound_to=depress (expected)"))
