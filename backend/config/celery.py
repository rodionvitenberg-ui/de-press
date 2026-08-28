"""Celery application for de-press backend."""

from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("depress")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(name="config.health_ping")
def health_ping() -> str:
    """No-op task used to verify broker connectivity."""
    return "pong"
