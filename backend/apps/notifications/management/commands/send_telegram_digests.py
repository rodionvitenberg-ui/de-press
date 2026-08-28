"""Run Telegram daily digests once (cron / manual; same logic as Celery beat)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.notifications.telegram_notify import run_telegram_daily_digests


class Command(BaseCommand):
    help = "Send opt-in Telegram daily digests for unread notifications."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Max accounts to process (default 500).",
        )

    def handle(self, *args, **options):
        limit = int(options.get("limit") or 500)
        stats = run_telegram_daily_digests(limit_accounts=limit)
        self.stdout.write(self.style.SUCCESS(f"Telegram digests: {stats}"))
