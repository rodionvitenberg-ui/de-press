"""Duty-fund lifecycle, report math, and public fund API (ADR-0020)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_tz

import pytest
from django.test import Client
from django.utils import timezone

from apps.fund.models import DutySegment
from apps.fund.services import (
    FundError,
    close_stale_for,
    duty_report,
    on_heartbeat,
    validate_tip_wallet,
)
from apps.identity.models import Account
from apps.identity.services import Actor, set_helper_duty

VALID_WALLET = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"


def make_helper(email: str, **kwargs) -> Account:
    return Account.objects.create_user(
        email=email, password="password123", is_helper=True, **kwargs
    )


def _dt(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=dt_tz.utc)


# --- Segment lifecycle ------------------------------------------------------


@pytest.mark.django_db
def test_duty_on_opens_segment_and_off_closes():
    acc = make_helper("fund-a@ex.com")
    actor = Actor(kind="account", account=acc)
    set_helper_duty(actor, True)
    assert DutySegment.objects.filter(helper=acc, ended_at__isnull=True).count() == 1
    set_helper_duty(actor, False)
    seg = DutySegment.objects.get(helper=acc)
    assert seg.ended_at is not None
    assert seg.close_reason == "manual"


@pytest.mark.django_db
def test_double_duty_on_keeps_single_open_segment():
    acc = make_helper("fund-b@ex.com")
    actor = Actor(kind="account", account=acc)
    set_helper_duty(actor, True)
    set_helper_duty(actor, True)
    assert DutySegment.objects.filter(helper=acc, ended_at__isnull=True).count() == 1


@pytest.mark.django_db
def test_manual_close_credits_until_last_heartbeat():
    acc = make_helper("fund-c@ex.com")
    actor = Actor(kind="account", account=acc)
    set_helper_duty(actor, True)
    # Shift began 30 minutes ago; the last heartbeat was 5 minutes ago.
    DutySegment.objects.update(started_at=timezone.now() - timedelta(minutes=30))
    seen = timezone.now() - timedelta(minutes=5)
    acc.helper_seen_at = seen
    acc.save(update_fields=["helper_seen_at"])
    set_helper_duty(actor, False)
    seg = DutySegment.objects.get(helper=acc)
    assert abs((seg.ended_at - seen).total_seconds()) < 1
    assert seg.close_reason == "manual"


@pytest.mark.django_db
def test_stale_close_credits_last_heartbeat():
    acc = make_helper("fund-d@ex.com")
    set_helper_duty(Actor(kind="account", account=acc), True)
    DutySegment.objects.update(started_at=timezone.now() - timedelta(minutes=60))
    seen = timezone.now() - timedelta(minutes=20)
    acc.helper_seen_at = seen
    acc.save(update_fields=["helper_seen_at"])
    close_stale_for(acc)
    seg = DutySegment.objects.get(helper=acc)
    assert seg.ended_at is not None
    assert abs((seg.ended_at - seen).total_seconds()) < 1
    assert seg.close_reason == "stale"
    acc.refresh_from_db()
    assert acc.is_on_duty is True


@pytest.mark.django_db
def test_heartbeat_after_gap_splits_stale_stretch():
    acc = make_helper("fund-e@ex.com")
    set_helper_duty(Actor(kind="account", account=acc), True)
    DutySegment.objects.update(started_at=timezone.now() - timedelta(minutes=60))
    prev_seen = timezone.now() - timedelta(minutes=30)
    on_heartbeat(acc, prev_seen=prev_seen)
    segments = DutySegment.objects.filter(helper=acc).order_by("started_at")
    assert segments.count() == 2
    stale, fresh = segments
    assert stale.close_reason == "stale"
    assert abs((stale.ended_at - prev_seen).total_seconds()) < 1
    assert fresh.ended_at is None
    # A fresh heartbeat does not open yet another segment.
    on_heartbeat(acc, prev_seen=timezone.now())
    assert DutySegment.objects.filter(helper=acc, ended_at__isnull=True).count() == 1


@pytest.mark.django_db
def test_heartbeat_ignores_off_duty():
    acc = make_helper("fund-f@ex.com")
    on_heartbeat(acc, prev_seen=timezone.now())
    assert DutySegment.objects.filter(helper=acc).count() == 0


# --- Report -----------------------------------------------------------------


@pytest.mark.django_db
def test_report_math_and_daily_cap():
    a = make_helper("fund-r1@ex.com", default_pseudonym="Ночной слушатель")
    b = make_helper("fund-r2@ex.com")
    DutySegment.objects.create(
        helper=a, started_at=_dt(2026, 5, 10, 8), ended_at=_dt(2026, 5, 10, 20)
    )  # 720 min in one UTC day -> capped to 600
    DutySegment.objects.create(
        helper=b, started_at=_dt(2026, 5, 11, 0), ended_at=_dt(2026, 5, 13, 16)
    )  # 3 days, each capped to 600 -> 1800
    DutySegment.objects.create(
        helper=b, started_at=_dt(2026, 4, 15, 0), ended_at=_dt(2026, 4, 16, 0)
    )  # other month -> excluded

    report = duty_report("2026-05")
    assert report["period"] == "2026-05"
    assert report["total_minutes"] == 2400
    rows = {row["pseudonym"]: row for row in report["rows"]}
    assert rows["Ночной слушатель"]["minutes"] == 600
    assert rows["Ночной слушатель"]["share_percent"] == 25.0
    anon_name = f"helper-{str(b.id)[:8]}"
    assert rows[anon_name]["minutes"] == 1800
    assert rows[anon_name]["share_percent"] == 75.0


@pytest.mark.django_db
def test_report_reconciles_stale_open_segment():
    acc = make_helper("fund-r3@ex.com")
    set_helper_duty(Actor(kind="account", account=acc), True)
    acc.helper_seen_at = timezone.now() - timedelta(minutes=30)
    acc.save(update_fields=["helper_seen_at"])
    duty_report()
    assert not DutySegment.objects.filter(helper=acc, ended_at__isnull=True).exists()


# --- Tip wallet validation ---------------------------------------------------


@pytest.mark.django_db
def test_validate_tip_wallet_accepts_and_clears():
    assert validate_tip_wallet(f"  {VALID_WALLET}  ") == VALID_WALLET
    assert validate_tip_wallet("") == ""
    assert validate_tip_wallet(None) == ""


@pytest.mark.django_db
def test_validate_tip_wallet_rejects_bad_input():
    for bad in ("abc", "0" * 40, "l" * 40, VALID_WALLET[:-1] + "0", "О" * 40):
        with pytest.raises(FundError):
            validate_tip_wallet(bad)


@pytest.mark.django_db
def test_validate_tip_wallet_rejects_treasury(settings):
    settings.TREASURY_SOLANA_ADDRESS = VALID_WALLET
    with pytest.raises(FundError):
        validate_tip_wallet(VALID_WALLET)


# --- HTTP contract -----------------------------------------------------------


@pytest.mark.django_db
def test_fund_info_defaults_empty():
    res = Client().get("/api/v1/fund/info")
    assert res.status_code == 200
    assert res.json() == {"treasury_address": "", "squads_url": ""}


@pytest.mark.django_db
def test_tip_wallet_requires_helper():
    assert (
        Client()
        .post(
            "/api/v1/me/tip-wallet",
            data={"address": VALID_WALLET},
            content_type="application/json",
        )
        .status_code
        == 403
    )
    plain = Account.objects.create_user(
        email="fund-plain@ex.com", password="password123"
    )
    c = Client()
    c.force_login(plain)
    assert (
        c.post(
            "/api/v1/me/tip-wallet",
            data={"address": VALID_WALLET},
            content_type="application/json",
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_tip_wallet_set_invalid_and_clear():
    acc = make_helper("fund-w@ex.com")
    c = Client()
    c.force_login(acc)
    assert (
        c.post(
            "/api/v1/me/tip-wallet",
            data={"address": "not-a-wallet"},
            content_type="application/json",
        ).status_code
        == 400
    )
    ok = c.post(
        "/api/v1/me/tip-wallet",
        data={"address": VALID_WALLET},
        content_type="application/json",
    )
    assert ok.status_code == 200
    acc.refresh_from_db()
    assert acc.tip_wallet_address == VALID_WALLET
    cleared = c.post(
        "/api/v1/me/tip-wallet", data={"address": ""}, content_type="application/json"
    )
    assert cleared.status_code == 200
    acc.refresh_from_db()
    assert acc.tip_wallet_address == ""


@pytest.mark.django_db
def test_fund_report_public_and_validates_period():
    acc = make_helper("fund-rep@ex.com", default_pseudonym="Дневной слушатель")
    DutySegment.objects.create(
        helper=acc, started_at=_dt(2026, 5, 10, 8), ended_at=_dt(2026, 5, 10, 18)
    )
    res = Client().get("/api/v1/fund/report?period=2026-05")
    assert res.status_code == 200
    body = res.json()
    assert body["period"] == "2026-05"
    assert body["total_minutes"] == 600
    assert body["rows"] == [
        {"pseudonym": "Дневной слушатель", "minutes": 600, "share_percent": 100.0}
    ]
    assert Client().get("/api/v1/fund/report?period=May").status_code == 400