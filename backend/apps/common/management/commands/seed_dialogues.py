"""Seed a demo Initiated Dialogue for local development."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.dialogue.models import Dialogue, DialogueIntent, DialogueSource, Message
from apps.dialogue.services import _create_dialogue, send_message
from apps.identity.models import Account, AnonymousSession
from apps.identity.services import Actor
from apps.stories.models import Story

SEED_EMAIL = "seed@de-press.local"
SEED_PASSWORD = "seedseed12"
PEER_PSEUDONYM = "слушатель-демо"


class Command(BaseCommand):
    help = (
        "Create one open demo Dialogue with messages if none exist "
        "(author = seed@de-press.local)"
    )

    def handle(self, *args, **options):
        if Dialogue.objects.exists():
            self.stdout.write("Dialogues already exist; skip seed.")
            return

        story = (
            Story.objects.filter(status="published")
            .order_by("published_at", "created_at")
            .first()
        )
        if story is None:
            self.stdout.write(
                self.style.ERROR(
                    "No published stories. Run: python manage.py seed_stories"
                )
            )
            return

        account, created = Account.objects.get_or_create(
            email=SEED_EMAIL,
            defaults={"default_pseudonym": "сеятель"},
        )
        # Known local password so /login shows author-side dialogues.
        account.set_password(SEED_PASSWORD)
        if not account.default_pseudonym:
            account.default_pseudonym = "сеятель"
        account.save()
        if created:
            self.stdout.write(f"Created seed account {SEED_EMAIL}")
        else:
            self.stdout.write(f"Reset local seed password for {SEED_EMAIL}")

        # Re-bind story author to seed account if needed (seed stories already do).
        if story.author_account_id != account.id:
            story = (
                Story.objects.filter(author_account=account, status="published")
                .order_by("published_at")
                .first()
            )
            if story is None:
                self.stdout.write(
                    self.style.ERROR(
                        "Seed account has no published stories. "
                        "Clear stories or re-seed."
                    )
                )
                return

        peer_session = AnonymousSession.objects.create(pseudonym=PEER_PSEUDONYM)
        peer = Actor(kind="anonymous", session=peer_session)
        author = Actor(kind="account", account=account)

        with transaction.atomic():
            dialogue = _create_dialogue(
                story=story,
                peer=peer,
                intent=DialogueIntent.LISTEN,
                source=DialogueSource.REQUEST,
                intro_body=(
                    "[система] Демо-диалог для локальной разработки. "
                    "Войди как seed@de-press.local / seedseed12, чтобы увидеть его в /me."
                ),
            )
            send_message(
                peer,
                dialogue.id,
                "Привет. Я просто хотел сказать, что ты не один(а) в этом.",
            )
            send_message(
                author,
                dialogue.id,
                "Спасибо, что рядом. Иногда этого достаточно.",
            )

        msg_count = Message.objects.filter(dialogue=dialogue).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded dialogue {dialogue.id} on story {story.id} "
                f"({msg_count} messages). "
                f"Login: {SEED_EMAIL} / {SEED_PASSWORD}"
            )
        )
