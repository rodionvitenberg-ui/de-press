"""Therapist contour models (ADR 0022).

The backend stores statuses and references only: it never touches keys,
payment proofs or balances. The Solana transfer goes client → therapist
directly; confirmation is manual (the therapist presses "paid").
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class TherapySessionStatus(models.TextChoices):
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
    PAYMENT_CLAIMED = "payment_claimed", "Client says payment sent"
    PAID = "paid", "Paid (therapist confirmed)"
    DECLINED = "declined", "Declined by therapist"
    DONE = "done", "Done"


class TherapistProfile(models.Model):
    """Therapist ≠ Helper (ADR-0010 stays): separate contour, admin invite."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="therapist_profile",
        help_text="Bound when the therapist claims the invite token.",
    )
    invite_token = models.CharField(max_length=64, unique=True)
    pseudonym = models.CharField(max_length=80)
    approach = models.CharField(max_length=300, blank=True, default="")
    languages = models.CharField(max_length=60, default="ru")
    rate_sol = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    solana_address = models.CharField(max_length=60, blank=True, default="")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Therapist profile"
        verbose_name_plural = "Therapist profiles"
        ordering = ("pseudonym",)

    def __str__(self) -> str:
        return f"therapist:{self.pseudonym} ({'active' if self.is_active else 'invited'})"


class TherapySession(models.Model):
    """Paid 1:1 session request: status machine, no money on the backend."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(
        TherapistProfile,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    client_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="therapy_sessions",
    )
    client_session = models.ForeignKey(
        "identity.AnonymousSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="therapy_sessions",
    )
    status = models.CharField(
        max_length=32,
        choices=TherapySessionStatus.choices,
        default=TherapySessionStatus.AWAITING_PAYMENT,
        db_index=True,
    )
    note = models.CharField(max_length=280, blank=True, default="")
    price_sol = models.DecimalField(max_digits=12, decimal_places=4)
    dialogue = models.OneToOneField(
        "dialogue.Dialogue",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="therapy_session",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Therapy session"
        verbose_name_plural = "Therapy sessions"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"tsession:{self.id}:{self.status}"
