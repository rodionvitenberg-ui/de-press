"""Non-custodial duty-fund accounting (ADR-0020).

The platform never moves money. This module records on-duty intervals
(DutySegment) and produces a transparent, pseudonymous hours report that
signers of the public Squads treasury use to split funds. Credit is
time-based: fake dialogues do not pay; a stale segment (no heartbeats) stops
accruing at the last heartbeat; a per-helper per-UTC-day cap bounds a
forgotten shift.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone as dt_timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from apps.identity.models import Account

from .models import DutySegment, DutySegmentCloseReason


class FundError(Exception):
    """Invalid fund/wallet input."""


_BASE58_ALPHABET = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


def validate_tip_wallet(address: str) -> str:
    """Validate an opt-in Solana tip address. Empty string clears it."""
    addr = (address or "").strip()
    if not addr:
        return ""
    if len(addr) < 32 or len(addr) > 44 or not set(addr) <= _BASE58_ALPHABET:
        raise FundError("Invalid Solana address")
    treasury = getattr(settings, "TREASURY_SOLANA_ADDRESS", "")
    if treasury and addr == treasury:
        raise FundError("Treasury address cannot be used as a tip wallet")
    return addr


# --- Ownership verification (ADR-0020 phase 2, off-chain) --------------------

# Canonical challenge signed by the injected wallet. Must stay byte-for-byte
# identical to the frontend builder in apps/*/src/features/fund/wallet.ts.
_CHALLENGE = (
    "de-press: verify wallet ownership\n"
    "This signature proves you control this Solana address.\n"
    "It grants no access to funds and expires in 10 minutes.\n"
    "Address: {address}\n"
    "Nonce: {nonce}"
)


def challenge_message(address: str, nonce: str) -> str:
    """Canonical message for signing; byte-identical to the frontend builder.

    The nonce is generated client-side and travels together with the
    signature, so the backend can rebuild the exact signed bytes without
    server-side state.
    """
    return _CHALLENGE.format(address=(address or "").strip(), nonce=nonce)


def tip_wallet_challenge(address: str) -> str:
    """Human-readable message the wallet signs to prove address ownership."""
    return challenge_message(address, secrets.token_hex(8))


def _b58decode(value: str) -> bytes:
    """Base58 decode without a dependency (32-byte ed25519 pubkey expected)."""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    base = len(alphabet)
    num = 0
    for char in value:
        index = alphabet.find(char)
        if index < 0:
            raise FundError("Invalid Solana address")
        num = num * base + index
    raw = num.to_bytes((num.bit_length() + 7) // 8, "big")
    # Leading '1's are leading zero bytes in the binary form.
    pad = len(value) - len(value.lstrip("1"))
    return b"\x00" * pad + raw


def verify_tip_wallet_signature(
    address: str, signature_b58: str, nonce: str = ""
) -> bool:
    """Check an ed25519 signature of the canonical challenge (off-chain).

    Only the address-format checks + local pubkey/signature math happen here:
    per ADR-0020 the backend never touches keys, transactions or RPC. The
    nonce is the one the signer embedded in the challenge.
    """
    signature = _b58decode(signature_b58)
    if len(signature) != 64:
        return False
    public_key = Ed25519PublicKey.from_public_bytes(_b58decode(address))
    try:
        public_key.verify(signature, challenge_message(address, nonce).encode("utf-8"))
    except InvalidSignature:
        return False
    return True


def _stale_gap() -> timedelta:
    return timedelta(minutes=int(settings.FUND_STALE_GAP_MINUTES))


def _open_segment(account: Account) -> DutySegment | None:
    return DutySegment.objects.filter(helper=account, ended_at__isnull=True).first()


def close_stale_for(account: Account, now: datetime | None = None) -> None:
    """Close the helper's open segment if duty is off or heartbeats stopped.

    A manual duty-off closes at the last heartbeat (or segment start); a
    stale segment (heartbeat gap) closes at the last heartbeat — not at now —
    so a closed laptop stops accruing credit.
    """
    now = now or timezone.now()
    segment = _open_segment(account)
    if segment is None:
        return
    last_seen = account.helper_seen_at
    if not account.is_on_duty:
        ended = min(now, last_seen) if last_seen else segment.started_at
        segment.ended_at = max(ended, segment.started_at)
        segment.close_reason = DutySegmentCloseReason.MANUAL
        segment.save(update_fields=["ended_at", "close_reason"])
        return
    if last_seen is None or (now - last_seen) > _stale_gap():
        ended = last_seen or segment.started_at
        segment.ended_at = max(ended, segment.started_at)
        segment.close_reason = DutySegmentCloseReason.STALE
        segment.save(update_fields=["ended_at", "close_reason"])


def on_duty_changed(account: Account) -> None:
    """Hook after set_helper_duty: reconcile, then open a segment if on duty."""
    close_stale_for(account)
    if account.is_on_duty:
        DutySegment.objects.get_or_create(
            helper=account,
            ended_at__isnull=True,
            defaults={"started_at": timezone.now()},
        )


def on_heartbeat(account: Account, prev_seen: datetime | None = None) -> None:
    """Hook from touch_helper, called before helper_seen_at is updated.

    Keeps exactly one open segment while on duty. A heartbeat after a long
    gap (> stale gap) ends the stale stretch at the previous heartbeat and
    starts a fresh segment at now, so the away time is never credited.
    """
    if not (account.is_helper and account.is_on_duty):
        return
    now = timezone.now()
    segment = _open_segment(account)
    if (
        segment is not None
        and prev_seen is not None
        and (now - prev_seen) > _stale_gap()
    ):
        segment.ended_at = max(prev_seen, segment.started_at)
        segment.close_reason = DutySegmentCloseReason.STALE
        segment.save(update_fields=["ended_at", "close_reason"])
        segment = None
    if segment is None:
        DutySegment.objects.get_or_create(
            helper=account,
            ended_at__isnull=True,
            defaults={"started_at": now},
        )


def _period_bounds(period: str) -> tuple[datetime, datetime]:
    try:
        start = datetime.strptime(period, "%Y-%m").replace(tzinfo=dt_timezone.utc)
    except (TypeError, ValueError) as exc:
        raise FundError("Period must be YYYY-MM") from exc
    if start.month == 12:
        next_year, next_month = start.year + 1, 1
    else:
        next_year, next_month = start.year, start.month + 1
    end = datetime(next_year, next_month, 1, tzinfo=dt_timezone.utc)
    return start, end


def _credited_seconds(
    start: datetime, end: datetime, period_start: datetime, period_end: datetime
) -> dict:
    """Per-UTC-day credited seconds for one segment inside the period."""
    per_day: dict = {}
    day_start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    while day_start < end:
        next_day = day_start + timedelta(days=1)
        seg_from = max(start, day_start, period_start)
        seg_to = min(end, next_day, period_end)
        if seg_to > seg_from:
            key = day_start.date()
            per_day[key] = per_day.get(key, 0.0) + (seg_to - seg_from).total_seconds()
        day_start = next_day
    return per_day


def duty_report(period: str | None = None) -> dict:
    """Transparent, pseudonymous duty-hours report for one UTC month.

    Reconciles stale open segments first, clamps credit per helper per UTC
    day (FUND_MAX_MINUTES_PER_DAY), and returns rows sorted by minutes.
    Helpers without a pseudonym appear as `helper-<id prefix>` — the report
    is public and must not leak email prefixes.
    """
    now = timezone.now()
    if not period:
        period = now.strftime("%Y-%m")
    period_start, period_end = _period_bounds(period)

    for account in Account.objects.filter(
        duty_segments__ended_at__isnull=True
    ).distinct():
        close_stale_for(account, now=now)

    cap_seconds = int(settings.FUND_MAX_MINUTES_PER_DAY) * 60
    segments = (
        DutySegment.objects.filter(started_at__lt=period_end)
        .filter(Q(ended_at__isnull=True) | Q(ended_at__gt=period_start))
        .select_related("helper")
    )
    per_helper_day: dict[int, dict] = {}
    helper_map: dict[int, Account] = {}
    for segment in segments:
        start = max(segment.started_at, period_start)
        end = min(segment.ended_at or now, period_end, now)
        if end <= start:
            continue
        helper_map[segment.helper_id] = segment.helper
        bucket = per_helper_day.setdefault(segment.helper_id, {})
        for day, seconds in _credited_seconds(start, end, period_start, period_end).items():
            bucket[day] = bucket.get(day, 0.0) + seconds

    rows: list[dict] = []
    total = 0
    for helper_id, bucket in per_helper_day.items():
        seconds_total = sum(min(secs, cap_seconds) for secs in bucket.values())
        minutes = int(seconds_total // 60)
        if minutes <= 0:
            continue
        helper = helper_map[helper_id]
        pseudonym = helper.default_pseudonym or f"helper-{str(helper.id)[:8]}"
        rows.append({"pseudonym": pseudonym, "minutes": minutes, "share_percent": 0.0})
        total += minutes
    for row in rows:
        row["share_percent"] = round(row["minutes"] / total * 100, 2) if total else 0.0
    rows.sort(key=lambda r: (-r["minutes"], r["pseudonym"]))
    return {"period": period, "total_minutes": total, "rows": rows}