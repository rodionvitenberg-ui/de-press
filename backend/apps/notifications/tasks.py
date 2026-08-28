"""Celery tasks for notifications (Telegram digests, …)."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.notifications.tasks.send_telegram_daily_digests")
def send_telegram_daily_digests(limit_accounts: int = 500) -> dict:
    """Periodic: soft Telegram digests for accounts with frequency=daily."""
    from apps.notifications.telegram_notify import run_telegram_daily_digests

    stats = run_telegram_daily_digests(limit_accounts=limit_accounts)
    logger.info("telegram daily digests: %s", stats)
    return stats
