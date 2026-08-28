"""Seed curated Quiet Phrases for private Support Clouds (ru + en)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.support.models import QuietPhrase

# Tone: silent empathy, no advice, no toxic positivity.
# Only three stay active; the rest remain in DB for old clouds.
ACTIVE_KEYS = frozenset({"i_am_here", "i_hear", "not_alone"})
PHRASES: list[tuple[str, str, str, int]] = [
    ("i_am_here", "Я рядом. Без слов.", "I'm here. No words needed.", 10),
    ("i_hear", "Слышу. Это тяжело.", "I hear you. This is hard.", 20),
    ("not_alone", "Ты не один(а) в этом.", "You're not alone in this.", 30),
    ("sit_with_you", "Я посижу с тобой молча.", "I'll sit with you in silence.", 40),
    ("breathe", "Дыши. Я рядом.", "Breathe. I'm nearby.", 50),
    (
        "valid",
        "То, что ты чувствуешь — понятно.",
        "What you feel is understandable.",
        60,
    ),
    (
        "no_rush",
        "Никуда не торопись. Можно просто быть.",
        "No rush. You can just be.",
        70,
    ),
    (
        "holding",
        "Держу пространство. Без советов.",
        "Holding space. No advice.",
        80,
    ),
    (
        "soft",
        "Мягко. Ты можешь не объяснять.",
        "Gently. You don't have to explain.",
        90,
    ),
    ("with_you", "С тобой. В тишине.", "With you. In quiet.", 100),
]


class Command(BaseCommand):
    help = "Upsert Quiet Phrase catalog (safe templates, ru+en)"

    def handle(self, *args, **options):
        created_n = 0
        updated_n = 0
        for key, text_ru, text_en, order in PHRASES:
            _, created = QuietPhrase.objects.update_or_create(
                key=key,
                defaults={
                    "text_ru": text_ru,
                    "text_en": text_en,
                    "sort_order": order,
                    "is_active": key in ACTIVE_KEYS,
                },
            )
            if created:
                created_n += 1
            else:
                updated_n += 1
        QuietPhrase.objects.exclude(key__in=ACTIVE_KEYS).update(is_active=False)
        self.stdout.write(
            self.style.SUCCESS(
                f"Quiet Phrases: created={created_n}, updated={updated_n}, "
                f"active={len(ACTIVE_KEYS)}"
            )
        )
