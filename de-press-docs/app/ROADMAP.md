# Roadmap de-press.co

See also [README.md](../README.md) (the stage and priorities), [CONTEXT.md](../CONTEXT.md), [PILOT.md](./PILOT.md).

## Stage (2026-08)

**Product core v0.0–v0.14 is closed in code.**  
**P1 "Soft-notify" is closed** (including the magic-token `/inbox` and `PUBLIC_BASE_URL` in settings).  
**Browser host (UI Core v2)** — a Vite SPA with TG ergonomics: the skeleton + the P0 push are closed.  
**Circles + voice retention on the server are closed.**  
Next for the product: the admin dashboard (moderation + reports, pre-launch) and the pilot readiness (the manual QA P6 — owner = human); the AI assistant and Geo-help v2 move after the launch (the owner's decision of 2026-08-31).  
By hosts: **Telegram Mini App ✅** (the stage is closed in code — initData auth, the theme bridge, bot soft-notify; the bot token/webhook — deploy-time config per DEPLOY.md), then — after the launch (≈ v1.3 / ≈ v1.5) — **own mobile** and **own desktop**.  
**The AI assistant and Geo-help v2 — moved after the launch (≈ v1.1 / ≈ v1.2).**  
The browser already has the Help human/AI paths (`/help`, `/help/wait`, `/help/ai` CompanionPane) — this is a companion surface, not the closed AI assistant.

**Therapy (ADR 0022, stage B) is closed in the browser and the Mini App** (Solana Pay QR + manual confirmation by the therapist). The questions of the new phase — [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md), the plan — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md).

> **Decision (2026-08, refined):** this repository is apps only.  
> **Four App Hosts:** browser · Telegram Mini App · own desktop · own mobile — see [`PLATFORMS.md`](./PLATFORMS.md), [ADR 0013](./adr/0013-four-app-hosts.md).  
> The Mini App is one platform and an interesting stage, **not** a replacement for own mobile/desktop.  
> The landing page is a separate repository; the connection is a jump link.

```
[ product core ✅ ]  [ soft-notify ✅ ]  [ browser UI core ✅ ]  [ circles/voice ✅ ]  [ ★ Mini App stage ]  [ multilingual ]  [ own mobile/desktop ]
```

## Phase decisions (2026-08-30 — all questions closed, details in [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md))

| Q | Decision |
|---|----------|
| Q1 voice/video | **A — status quo:** live voice and circles live inside the 1:1 dialogue, the role does not matter (human↔human is allowed) |
| Q2 calls in the Mini App | **We port them** — call.* + signaling over the dialogue WS, parity with the browser (plan P1.3) |
| Q3 helper dashboard | **A:** a left tab, visible to helpers only; we evolve the existing `/helper` |
| Q4 dashboard realtime | **A WS queue channel from the start**, no polling |
| Q5 repository | **GitHub publication is the LAST task of the whole project** (after everything else closes); license, CI, README — at the moment of publication |
| Q6 documentation | **EN is canon**; the RU versions are copied to `docs-ru-archive/` at the root before the translation, the folder is in `.gitignore` |
| Q7 calling a helper directly | **No** — a call only inside the dialogue |
| Q8 dashboard metrics | **Accepted:** the queue, the median wait, taken/closed per period, duty; no per-helper seconds, ratings, or engagement |
| Q9 retest | **A:** a manual checklist per the extended PILOT smoke; Playwright — after the pilot |
| Q10 anonymous users and therapy | **We keep it.** Invariants: an anonymous user has the same capabilities as a registered one; **all history always lives in the user's browser, not with us** |

## Already done

| Version | Content | Status |
|---------|---------|--------|
| v0.0–v0.7 | Foundation, safety, monologue, dialogue, Anti-Panic, AI, ZK patterns, help static | ✅ |
| WS | Channels, typing, reconnect | ✅ |
| Pilot docs | PILOT.md, smoke | ✅ |
| **v0.9** | Quiet Phrases + private Support Clouds (templates) | ✅ |
| **v0.10** | Hearer List + Author Outreach | ✅ |
| **v0.11** | Moderated free-text + Helper + queue | ✅ |
| **v0.12** | Design pass (clouds, author vs public) | ✅ |
| **v0.13** | i18n ru/en + phrase texts | ✅ |
| **v0.14** | Voice notes + translate | ✅ |
| **P1 notify (full)** | Notification + EmailDigest + WS + REST + settings + `/inbox` + `PUBLIC_BASE_URL` | ✅ |

## P1 "Soft-notify" — closed ✅

- ✅ `Notification` (kind, payload, is_read) + `EmailDigest` (magic token, statuses) + migrations
- ✅ REST: `/me/notifications`, `unread-count`, `mark-read`, `read-all`
- ✅ WS `/ws/notifications/` (snapshot, new, read, unread_count, ping) + the Anti-Panic kill
- ✅ `notify()` from dialogue and support (dialogue requests, clouds, approve, messages, outreach)
- ✅ `/me/notify-settings` (opt-in, frequency, contact email) + the digest test
- ✅ **`POST /auth/inbox`** — sign-in via a magic token (account → login, anon → bind the anon cookie)
- ✅ **The `/inbox` page** (`?token=...`) — opens the private inbox, marks the read ones
- ✅ **`PUBLIC_BASE_URL`** moved into settings/env (softnotify uses `settings.PUBLIC_BASE_URL`)
- ✅ Tests: open_inbox (account/anon/invalid) + tsc clean

## Next (the new priority order)

| Priority | Content |
|----------|---------|
| **P0 ✅** | **UI Core / Browser host**: Vite + React SPA, tokens/themes, the 3-zone TG skeleton, feed/chat, "I'M NOT OK" |
| **P0 ✅** | **Circles**: `POST …/messages/circle` + an ephemeral purge on close |
| **P0 ✅** | **Voice notes with a delete option**: `/me/voice-retention` + a per-sender purge on close |
| **P0 ✅** | **The browser ↔ Mini App parity tails**: the fund (FundCard/TipBanner/TipWalletForm), calls in the Mini App (Q2: we port them); therapy in the Mini App ✅ |
| **P0 ✅** | **The helper dashboard**: a left tab, visible to helpers only; the queue over a WS channel from the start (Q4), take → dialogue, the summary — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md) |
| **P0 ✅** | **The docs translation into EN (the RU archive in `docs-ru-archive/`, gitignored) + the full retest → manual QA** (the automated part done; the manual smoke matrix — P6, owner = human) — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md) |
| 🗄 dropped | **Native dynamic multilingual** (STT → translate → TTS) — dropped: cannot be implemented adequately without keys; text translation remains |
| **P1 ✅** | **Telegram Mini App host (a stage)**: Bot + Mini App, initData auth, the theme bridge, optional bot soft-notify; the dialogues stay on the de-press backend — **not** a replacement for own mobile |
| **P1 ★ (pre-launch)** | **The admin dashboard** — a separate Vite app, `apps/admin`, staff-only: the aggregate overview (the visitors, the public posts — counts only, no identities), the reports queue with the mandatory-reason resolution + the audit log, the hide/remove of the reported content, the reports panel for the helpers in `/helper` — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md) P7 |
| **P1 → after the launch (≈ v1.3)** | **Own Mobile**: the TG tab-bar layout → a PWA / a native wrapper / a store (a separate host); frozen until after the launch |
| **P1 → after the launch (≈ v1.5)** | **Own Desktop**: a UI Core wrapper (Tauri / Electron — the decision later); frozen until after the launch |
| **P1 ✅** | **PWA bridge on the browser host** — installable standalone + phone/tablet chrome; a native store still later. The prod build is verified (manifest+icons 200, sw.js served, the install row in More, the offline shell per sw.js); a live phone install — pilot QA. See [`MOBILE_PWA.md`](./MOBILE_PWA.md). The further polish is frozen until after the pilot |
| 🗄 → landing | **Public pages (help, guides)** — moved to the landing repo (the guides were cut on 2026-08-30; in the app `/help` is the gate only) |
| **P1** | Pilot ops: staging, a closed cohort, a feedback loop; the deploy kit: [`DEPLOY.md`](./DEPLOY.md) |
| **P1** | Helper onboarding; ethical ops metrics; media/S3; secrets/backup |
| **→ after the launch (≈ v1.2)** | Geo-help v2; pre-mod / AI-assist for reports |
| **→ after the launch (≈ v1.1)** | **The AI assistant** — right after the launch; the publication (Q5) happens without it |
| **after everything** | **Publishing the repository on GitHub** (license, CI, README) — the last task of the project, after all the others are closed (Q5) |

The version ladder (approximate, per the owner's sketch of 2026-08-31): **1.0** — the launch line: the admin dashboard + the moderation/reports workflow, the pilot, then the publication (Q5 — the AI assistant is no longer a blocker; the apps are bumped 0.1.0 → 1.0.0); **1.1** — the AI assistant; **1.2** — Geo-help v2 + pre-mod/AI-assist for the reports; **1.3** — own mobile; **1.5** — own desktop.

## Voice

1. ✅ A voice note in the Dialogue
2. 🗄 STT — dropped (offline stubs are no good; cannot be implemented adequately without keys)
3. ✅ Translate (an LLM gateway or an offline marker)
4. ✅ **Circles** (video circles) — self-destruct when the chat closes
5. ✅ **Voice notes with a delete option** (configurable, per-sender)
6. 🗄 **Native dynamic translation** (STT → translate → TTS) — dropped; text translation remains
7. ✅ **Live 1:1 voice in the dialogue** (ADR 0021, signaling over the dialogue WS, self-hosted TURN/STUN); group rooms — still not doing

## The "clouds" model (accepted)

**Public:** the monologue + "I hear you" + quiet phrases (no trace) + a dialogue request.  
**For the author:** the Hearer List (if there is someone to write to), the cloud gesture on their own feed row, the inbox of dialogue requests, the chat. No pulse and no cloud list in the UI (ADR 0017).

| Channel | Moderation | Visibility |
|---------|-----------|------------|
| Silent Empathy / rays | none | removed from the UI (ADR 0018); the Pulse/hearers API is alive |
| Quiet Phrase | none | a gesture on their own feed row; not a list, not a bell |
| Moderated Cloud | manual | the same after approve; the Helper queue |
| Dialogue | post-mod / report | 1-1 |

Invariant: **no** public comments, likes, or reaction showcases on an entry page.

## The fund (ADR 0020) — done in the browser SPA and the Mini App

A non-custodial contour: a public treasury (a Squads multisig, `TREASURY_SOLANA_ADDRESS` — empty = the UI is hidden), a helper's opt-in tip wallet (visible only in a closed dialogue to the grateful peer, with the "a separate wallet" warning), the duty fund with a per-day cap and a lazy stale-close, a public pseudonymous report `GET /v1/fund/report?period=YYYY-MM` — the multisig signers split the treasury by it. Money moves only wallet → wallet; the backend never touches keys, payments, or RPC.
Done: the ownership verification by signature (phase 2) — an off-chain ed25519 proof of the tip-wallet ownership, surfaced as the "verified" badge. The public report page goes to the promo/landing repo, not the app (the owner's decision of 2026-08-31) — the API `GET /v1/fund/report` stays as is; nothing left in the app for ADR-0020.

## Therapy (ADR 0022) — a seedling

A therapist catalog (access by an admin invite), a profile (pseudonym, approach,
languages, the rate in SOL, a Solana address), a session request by the client → `awaiting_payment`
→ a Solana Pay QR (a direct client → therapist transfer; ADR 0020 is untouched) →
"I paid" → **manual confirmation by the therapist** → `paid` → a 1:1 dialogue and
a live call (ADR 0021) as the session channel. The backend stores only statuses and
references: no keys, no payment processing, no money balances. Plan:
[`VOICE_THERAPY_PLAN.md`](./VOICE_THERAPY_PLAN.md).

## Not doing

