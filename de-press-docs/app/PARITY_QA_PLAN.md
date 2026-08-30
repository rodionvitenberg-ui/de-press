# Plan: parity, the helper dashboard, the translation, the retest (August 2026)

Related: [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md) (the questions Q1–Q10), [ROADMAP.md](./ROADMAP.md), [VOICE_THERAPY_PLAN.md](./VOICE_THERAPY_PLAN.md) (closed).

Principles: minimal diffs; parity = porting the existing, not new features; every step ends with green checks and a commit. All questions are resolved 2026-08-30 — the summary in [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md) and the "Phase decisions" of [ROADMAP.md](./ROADMAP.md).

## P1. The browser ↔ Mini App parity tails

| Step | What | Status |
|------|------|--------|
| P1.1 | **Therapy in the Mini App**: TherapyPane + PayModal (a Solana Pay QR), the api methods and types (`TherapistProfileOut`/`TherapySession`/`Me.is_therapist`), i18n `therapy.*` (31 keys) + `nav.therapy`, an icon in the Sidebar rail, the `qrcode` dep | ✅ done |
| P1.2 | **The fund in the Mini App**: FundCard, TipBanner (DialoguePage), TipWalletForm (UserMenu), `wallet.ts` (the test stayed in the browser — the same logic, no vitest in the mini-app), the api `fundInfo`/`setTipWallet`, i18n `fund.*` (15 keys) | ✅ done |
| P1.3 | **Calls in the Mini App**: we port them (Q2) — callMachine/useCall/CallModal, the signaling over the dialogue WS (`CallSignalEvent`+`sendCall` in useChatSocket), the api `rtcConfig`, the button hidden without `navigator.mediaDevices`, i18n `calls.*` (17 keys) | ✅ done |

Acceptance: `npm run build` (tsc + vite) in the mini-app is green; i18n is in sync ru/en/types; the total catalog is ≤ 640 keys (the shared cap `i18n_ui.MAX_KEYS`).

## P2. Publishing the repository — at the very end of the project (Q5)

The Q5 decision: the GitHub publication is deferred until all the other project tasks are closed.
- At the moment of publication: the license (AGPL-3.0), CI (GitHub Actions: ruff + pytest in chunks, vitest, both vite builds), README (a quick start, the stack, the structure).
- Before publication: `git log --format=%ae | sort -u` (the emails in the history), `.env.example` checked against `settings/base.py`.

## P3. Translating the documentation into EN

- Inventory: 15 docs in `de-press-docs/app` + 22 ADR + 6 at the root = **43 files** (~2.6k lines).
- First the glossary (Q6), then in batches: the root (README, PRIVACY, CONTEXT, MAINPLAN, PROGRESS) → the app docs → the ADR.
- Format: EN replaces RU (resolved Q6-A); before the translation the RU versions are copied to `docs-ru-archive/` at the project root, the folder is in `.gitignore`.

## P4. The full retest

- **Backend** (in chunks, a ~30s runner timeout): therapy, fund, identity, common+notifications, dialogue, ai (`env -u DEEPSEEK_API_KEY`), empathy+moderation, support, stories.
- **Frontend:** browser vitest 64 + tsc + build; the mini-app build.
- **The smoke matrix** for the manual check (P6): anti-panic · feed+clouds · quiet phrases · dialogue+voice+circles · help human/AI · helper (the queue, duty, invites) · the ZK patterns · notifications+`/inbox` · the fund (the wallet/banner/report) · therapy (invite → catalog → session → QR → "I paid" → confirmation → dialogue) · the i18n switch · all the same in the Mini App inside Telegram.

## P5. The helper dashboard

- A left tab (browser), visible to `is_helper` only; the existing `/helper` (HelperQueue) evolves into the dashboard.
- The v1 composition: a live request queue over a WS channel from the start (Q4; the notifications-WS pattern), "take" → opening the dialogue (the call button is already in the dialogue), the duty status (the existing toggle), the summary (the existing one), the metrics from Q8.
- A user starting a conversation with a helper already works via a help request; no direct calls (Q7).
- The design by the DESIGN_V2 tokens; backend tests for new endpoints, if any appear.

## P6. Manual QA

The readiness criteria: P1–P5 are closed, the P4 smoke matrix is done, the known limitations are recorded in PROGRESS. Next — the pilot (pilot ops in the ROADMAP).
