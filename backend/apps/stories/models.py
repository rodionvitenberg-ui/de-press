"""Story (Safe Monologue) domain model."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def story_voice_upload_to(instance: "Story", filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    if ext not in {"webm", "ogg", "mp3", "m4a", "wav", "mp4"}:
        ext = "webm"
    return f"story_voice/{instance.id}.{ext}"


class StoryStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    HIDDEN = "hidden", "Hidden"
    REMOVED = "removed", "Removed"


class StoryTopic(models.TextChoices):
    """Fixed themes — no free-tag chaos."""

    LONELINESS = "loneliness", "Одиночество"
    ANXIETY = "anxiety", "Тревога"
    GRIEF = "grief", "Горе / утрата"
    EXHAUSTION = "exhaustion", "Выгорание"
    RELATIONSHIPS = "relationships", "Отношения"
    SELF = "self", "Отношение к себе"
    CRISIS = "crisis", "Кризисный момент"
    OTHER = "other", "Другое"


class Story(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    body = models.TextField(blank=True)
    audio = models.FileField(
        upload_to=story_voice_upload_to,
        blank=True,
        null=True,
        max_length=512,
    )
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    topic = models.CharField(
        max_length=32,
        choices=StoryTopic.choices,
        default=StoryTopic.OTHER,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=StoryStatus.choices,
        default=StoryStatus.PUBLISHED,
        db_index=True,
    )
    author_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stories",
    )
    author_session = models.ForeignKey(
        "identity.AnonymousSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stories",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    last_activity_at = models.DateTimeField(null=True, blank=True, db_index=True)
    clouds_last_read_at = models.DateTimeField(null=True, blank=True)
    pseudonym_snapshot = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Story"
        verbose_name_plural = "Stories"
        ordering = ("-published_at", "-created_at")
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(author_account__isnull=False) & Q(author_session__isnull=True))
                    | (Q(author_account__isnull=True) & Q(author_session__isnull=False))
                ),
                name="story_exactly_one_author",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(
                fields=["status", "-last_activity_at"],
                name="stories_sto_status_act_idx",
            ),
        ]

    def clean(self) -> None:
        has_account = self.author_account_id is not None
        has_session = self.author_session_id is not None
        if has_account == has_session:
            raise ValidationError("Story must have exactly one of author_account or author_session")

    def __str__(self) -> str:
        preview = (self.body[:48] + "…") if len(self.body) > 48 else self.body
        return preview
