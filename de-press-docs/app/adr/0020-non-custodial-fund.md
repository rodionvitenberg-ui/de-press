# Non-custodial public fund: treasury, listener tips, duty hours

## Status

Accepted (2026-08).

## Context

The platform needs a funding contour (Web3 microgrant requirement) that is compatible with its core claim — «анонимность по архитектуре». Any server-side payment handling (custody, keys, commissions, KYC, RPC infrastructure) would turn a privacy-verifiable product into a money processor. At the same time the project wants: a public treasury with transparent spend, a way for grateful peers to thank a listener directly, and honest accounting of helper duty hours.

## Decision

1. **Non-custodial boundary.** The backend never touches private keys, transactions, commissions or RPC. Money moves only on-chain, wallet-to-wallet. No payment code exists in the backend.
2. **Treasury = public Squads Multisig vault.** Settings `TREASURY_SOLANA_ADDRESS` + `TREASURY_SQUADS_URL` (empty = the fund UI is hidden). Signers distribute funds manually; the platform only displays the address.
3. **Listener tips = opt-in.** `Account.tip_wallet_address` (base58, 32–44 chars, ≠ treasury) is set by the helper and exposed **only** as `peer_tip_wallet` on a **closed** dialogue where the peer is the helper — never on public stories or open dialogues. UI warns to use a dedicated wallet (on-chain tips are linkable).
4. **Duty fund = time-based credit, not per-dialogue.** `apps/fund.DutySegment` ledger: opened on duty-on, closed by duty-off at the last heartbeat, closed **lazily** when heartbeats stop (`FUND_STALE_GAP_MINUTES=15` — credited up to the last heartbeat, no celery), credit capped per helper per UTC day (`FUND_MAX_MINUTES_PER_DAY=600`) — fake-dialogue farming does not pay, a forgotten shift does not inflate. Public pseudonymous report `GET /v1/fund/report?period=YYYY-MM` → `{pseudonym, minutes, share_percent}`; helpers without a pseudonym appear as `helper-<id prefix>` (an email prefix must never leak into a public page). Signers split the treasury using this report.
5. **Deep links, not QR libraries.** `solana:<address>?spl-token=<USDC mint>` — YAGNI on any wallet/QR dependency.

## Consequences

- Zero payment surface on the backend keeps the grant claim verifiable by code; no custody/compliance risk is introduced.
- Stale segments are reconciled lazily (duty toggle, heartbeat, report read) — no background worker needed.
- The i18n catalog cap was raised 500 → 560 (`apps/common/i18n_ui.py`; keep `flatten.test.ts` in sync) — the browser SPA fund strings needed it, the catalog was already at 495.
- Mini App parity for the fund contour is a separate next track.

## Non-goals

- No backend payments/keys/RPC, no auto-payouts, no QR library.
- No on-chain signature-ownership verification (phase 2).
- No fund-report page in the browser SPA (public API only for now).