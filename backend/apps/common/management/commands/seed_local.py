"""Orchestrate local demo seeds against Postgres `depress`."""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "seed_stories + seed_quiet_phrases + seed_dialogues (local Postgres)"

    def handle(self, *args, **options):
        call_command("check_db")
        call_command("seed_stories")
        call_command("seed_quiet_phrases")
        call_command("seed_dialogues")
        self.stdout.write("")
        call_command("check_db")
        self.stdout.write(
            self.style.SUCCESS(
                "Local seed complete. Feed: public stories. "
                "Chats: login seed@de-press.local / seedseed12 → /me"
            )
        )
