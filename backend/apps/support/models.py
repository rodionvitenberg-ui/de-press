"""Quiet Phrases catalog and private Support Clouds."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class QuietPhrase(models.Model):
    """Curated safe template for one-click private Support Clouds."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.SlugField(max_length=64, unique=True)
    text_ru = models.CharField(max_length=280)
    text_en = models.CharField(max_length=280, blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    image = models.FileField(upload_to="quiet_phrases/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Quiet Phrase"
        verbose_name_plural = "Quiet Phrases"
        ordering = ("sort_order", "key")

    def __str__(self) -> str:
        return f"{self.key}: {self.text_ru[:40]}"


class SupportCloudKind(models.TextChoices):
    QUIET_PHRASE = "quiet_phrase", "Quiet Phrase"
    FREE_TEXT = "free_text", "Free text (moderated)"


class SupportCloudStatus(models.TextChoices):
    DELIVERED = "delivered", "Delivered"
    PENDING = "pending", "Pending moderation"
    REJECTED = "rejected", "Rejected"


class SupportCloud(models.Model):
    """Private support note attached to a Story; author-only visibility."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(
        "stories.Story",
        on_delete=models.CASCADE,
        related_name="support_clouds",
    )
    from_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="support_clouds_sent",
    )
    from_session = models.ForeignKey(
        "identity.AnonymousSession",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="support_clouds_sent",
    )
    kind = models.CharField(
        max_length=32,
        choices=SupportCloudKind.choices,
        default=SupportCloudKind.QUIET_PHRASE,
        db_index=True,
    )
    phrase = models.ForeignKey(
        QuietPhrase,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clouds",
    )
    body_snapshot = models.CharField(max_length=500)
    pseudonym_snapshot = models.CharField(max_length=64)
    # Snapshotted at send time so author badge stays stable (ADR-0010).
    helper_badge = models.CharField(max_length=140, blank=True, default="")
    is_priority = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=SupportCloudStatus.choices,
        default=SupportCloudStatus.DELIVERED,
        db_index=True,
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clouds_moderated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    dismissed_by_author = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Support Cloud"
        verbose_name_plural = "Support Clouds"
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        Q(from_account__isnull=False)
                        & Q(from_session__isnull=True)
                    )
                    | (
                        Q(from_account__isnull=True)
                        & Q(from_session__isnull=False)
                    )
                ),
                name="support_cloud_exactly_one_sender",
            ),
            models.UniqueConstraint(
                fields=["story", "from_account"],
                condition=Q(from_account__isnull=False) & ~Q(status="rejected"),
                name="unique_cloud_per_account_story",
            ),
            models.UniqueConstraint(
                fields=["story", "from_session"],
                condition=Q(from_session__isnull=False) & ~Q(status="rejected"),
                name="unique_cloud_per_session_story",
            ),
        ]
        indexes = [
            models.Index(fields=["story", "status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"cloud:{self.story_id}:{self.kind}"
