"""Silent Empathy and Empathy Pulse."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class SilentEmpathy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(
        "stories.Story",
        on_delete=models.CASCADE,
        related_name="empathies",
    )
    from_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="empathies_given",
    )
    from_session = models.ForeignKey(
        "identity.AnonymousSession",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="empathies_given",
    )
    # Author Outreach consent: default on; Hearer may opt out (ADR-0009).
    outreach_opt_in = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Silent Empathy"
        verbose_name_plural = "Silent Empathies"
        constraints = [
            models.UniqueConstraint(
                fields=["story", "from_account"],
                condition=models.Q(from_account__isnull=False),
                name="unique_empathy_per_account_story",
            ),
            models.UniqueConstraint(
                fields=["story", "from_session"],
                condition=models.Q(from_session__isnull=False),
                name="unique_empathy_per_session_story",
            ),
        ]

    def __str__(self) -> str:
        return f"empathy:{self.story_id}"


class EmpathyPulse(models.Model):
    """Author-private aggregate count for a Story."""

    story = models.OneToOneField(
        "stories.Story",
        on_delete=models.CASCADE,
        related_name="pulse",
        primary_key=True,
    )
    count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empathy Pulse"
        verbose_name_plural = "Empathy Pulses"

    def __str__(self) -> str:
        return f"pulse:{self.story_id}={self.count}"
