"""Public non-custodial fund endpoints (ADR-0020).

No payments ever touch the backend: these endpoints only expose the public
treasury addresses, the opt-in helper tip wallet, and the transparent
duty-hours report used by the Squads Multisig signers.
"""

from __future__ import annotations

from django.conf import settings
from ninja import Router, Schema
from ninja.errors import HttpError

from apps.fund.services import (
    FundError,
    duty_report,
    validate_tip_wallet,
    verify_tip_wallet_signature,
)
from apps.identity.services import resolve_actor
from django.utils import timezone

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
    # ADR-0020 phase 2: optional base58 ed25519 signature of the canonical
    # challenge plus the nonce embedded in it (see apps.fund.services).
    signature: str = ""
    nonce: str = ""


class TipWalletOut(Schema):
    ok: bool
    tip_wallet_address: str
    tip_wallet_verified: bool


@router.post("/me/tip-wallet", response=TipWalletOut)
def post_tip_wallet(request, payload: TipWalletIn):
    """Helper-only opt-in: publish (or clear) a personal Solana tip address.

    Setting a new address without a signature publishes it unverified; a
    signature over the canonical challenge proves ownership off-chain. An
    empty address always clears both the address and its proof.
    """
    actor = resolve_actor(request)
    account = actor.account
    if account is None or not account.is_helper:
        raise HttpError(403, "Only a Helper can set a tip wallet")
    try:
        address = validate_tip_wallet(payload.address)
    except FundError as exc:
        raise HttpError(400, str(exc)) from exc
    if not address:
        account.tip_wallet_address = ""
        account.tip_wallet_verified_at = None
        account.save(update_fields=["tip_wallet_address", "tip_wallet_verified_at"])
        return TipWalletOut(ok=True, tip_wallet_address="", tip_wallet_verified=False)
    verified_at = None
    if payload.signature:
        if not payload.nonce:
            raise HttpError(400, "Missing challenge nonce for the signature")
        try:
            signed_ok = verify_tip_wallet_signature(
                address, payload.signature, payload.nonce
            )
        except FundError as exc:
            raise HttpError(400, str(exc)) from exc
        if not signed_ok:
            raise HttpError(400, "Signature does not prove ownership of this address")
        verified_at = timezone.now()
    elif account.tip_wallet_address != address:
        # A different address without proof: keep the old verified_at only when
        # the address is unchanged, otherwise the badge must not survive.
        account.tip_wallet_verified_at = None
    if verified_at is not None:
        account.tip_wallet_verified_at = verified_at
    account.tip_wallet_address = address
    account.save(update_fields=["tip_wallet_address", "tip_wallet_verified_at"])
    return TipWalletOut(
        ok=True,
        tip_wallet_address=address,
        tip_wallet_verified=account.tip_wallet_verified_at is not None,
    )


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