"""Public non-custodial fund endpoints (ADR-0020).

No payments ever touch the backend: these endpoints only expose the public
treasury addresses, the opt-in helper tip wallet, and the transparent
duty-hours report used by the Squads Multisig signers.
"""

from __future__ import annotations

from django.conf import settings
from ninja import Router, Schema
from ninja.errors import HttpError

from apps.fund.services import FundError, duty_report, validate_tip_wallet
from apps.identity.services import resolve_actor

router = Router(tags=["fund"])


class FundInfoOut(Schema):
    treasury_address: str = ""
    squads_url: str = ""


@router.get("/fund/info", response=FundInfoOut)
def fund_info(request):
    """Public treasury info. Empty address = fund block hidden in UI."""
    return FundInfoOut(
        treasury_address=getattr(settings, "TREASURY_SOLANA_ADDRESS", "") or "",
        squads_url=getattr(settings, "TREASURY_SQUADS_URL", "") or "",
    )


class TipWalletIn(Schema):
    address: str = ""


class TipWalletOut(Schema):
    ok: bool
    tip_wallet_address: str


@router.post("/me/tip-wallet", response=TipWalletOut)
def post_tip_wallet(request, payload: TipWalletIn):
    """Helper-only opt-in: publish (or clear) a personal Solana tip address."""
    actor = resolve_actor(request)
    account = actor.account
    if account is None or not account.is_helper:
        raise HttpError(403, "Only a Helper can set a tip wallet")
    try:
        address = validate_tip_wallet(payload.address)
    except FundError as exc:
        raise HttpError(400, str(exc)) from exc
    account.tip_wallet_address = address
    account.save(update_fields=["tip_wallet_address"])
    return TipWalletOut(ok=True, tip_wallet_address=address)


class FundReportRowOut(Schema):
    pseudonym: str
    minutes: int
    share_percent: float


class FundReportOut(Schema):
    period: str
    total_minutes: int
    rows: list[FundReportRowOut]
    treasury_address: str = ""


@router.get("/fund/report", response=FundReportOut)
def fund_report_view(request, period: str | None = None):
    """Public pseudonymous duty-hours report (UTC month, YYYY-MM)."""
    try:
        report = duty_report(period)
    except FundError as exc:
        raise HttpError(400, str(exc)) from exc
    return FundReportOut(
        period=report["period"],
        total_minutes=report["total_minutes"],
        rows=[FundReportRowOut(**row) for row in report["rows"]],
        treasury_address=getattr(settings, "TREASURY_SOLANA_ADDRESS", "") or "",
    )