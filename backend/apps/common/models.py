"""Shared abstract models."""

from __future__ import annotations

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPrimaryKeyModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BugReport(TimeStampedModel, UUIDPrimaryKeyModel):
    """A bug a user filed from the UI; staff triages it in admin."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        DONE = "done", "Done"

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NEW
    )
    reporter_account = models.ForeignKey(
        "identity.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bug_reports",
    )
    reporter_session = models.ForeignKey(
        "identity.AnonymousSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bug_reports",
    )
    text = models.TextField()
    page = models.CharField(max_length=200, blank=True, default="")
    user_agent = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"[{self.status}] {self.text[:60]}"
