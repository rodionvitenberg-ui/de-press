"""Seed sample published stories for local development."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.identity.models import Account
from apps.identity.services import Actor
from apps.stories.models import Story
from apps.stories.services import publish_story

SAMPLES = [
    ("Иногда просто нужно, чтобы кто-то был рядом — без советов и «держись».", "loneliness"),
    ("Сегодня встал с кровати. Это уже победа, даже если больше ничего не вышло.", "exhaustion"),
    ("Мне страшно писать вслух. Но здесь, кажется, можно тихо.", "anxiety"),
]


class Command(BaseCommand):
    help = "Create sample Stories if the feed is empty"

    def handle(self, *args, **options):
        helper, helper_created = Account.objects.get_or_create(
            email="helper@de-press.local",
            defaults={
                "default_pseudonym": "helper",
                "is_helper": True,
                "helper_org": "pilot",
            },
        )
        if helper_created:
            helper.set_password("helperhelper12")
            helper.save()
            self.stdout.write(self.style.SUCCESS("Created helper@de-press.local"))
        elif not helper.is_helper:
            helper.is_helper = True
            helper.helper_org = "pilot"
            helper.default_pseudonym = "helper"
            helper.save(
                update_fields=["is_helper", "helper_org", "default_pseudonym"]
            )
            self.stdout.write(self.style.SUCCESS("Updated helper@de-press.local flags"))

        if Story.objects.exists():
            self.stdout.write("Stories already exist; skip seed.")
            return

        account, created = Account.objects.get_or_create(
            email="seed@de-press.local",
            defaults={"default_pseudonym": "сеятель"},
        )
        if created:
            account.set_password("seed-not-for-login")
            account.save()

        actor = Actor(kind="account", account=account)
        for body, topic in SAMPLES:
            publish_story(actor, body, topic=topic)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(SAMPLES)} stories."))
