"""Duty-fund models: transparent on-duty credit ledger (ADR-0020)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class DutySegmentCloseReason(models.TextChoices):
    MANUAL = "manual", "Duty toggled off"
    STALE = "stale", "Heartbeat gap"


class DutySegment(models.Model):
    """One credited on-duty interval of a Helper.

    Opened when the helper goes on duty, closed by duty-off (manual) or
    lazily when heartbeats stop (stale). Credit is time-based: fake dialogues
    do not pay. The platform never moves money — signers of the public
    Squads treasury split funds using the aggregated hours report.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    helper = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="duty_segments",
    )
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True, db_index=True)
    close_reason = models.CharField(
        max_length=16,
        choices=DutySegmentCloseReason.choices,
        blank=True,
        default="",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Duty segment"
        verbose_name_plural = "Duty segments"
        ordering = ("-started_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["helper"],
                condition=Q(ended_at__isnull=True),
                name="fund_one_open_segment_per_helper",
            ),
        ]
        indexes = [
            models.Index(fields=["helper", "-started_at"]),
        ]

    def __str__(self) -> str:
        return f"duty:{self.helper_id}:{self.started_at:%Y-%m-%d}"