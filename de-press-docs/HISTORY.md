# The history of de-press — how I built it

> This is not technical documentation but the story of how the project appeared, what I
> cancelled along the way, and where it stands now. Everything written here can be checked:
> the work journal is in [`PROGRESS.md`](../../PROGRESS.md), the architectural decisions are
> in [`adr/`](./app/adr/), the code is in git. First written 2026-08-30, right after the
> deploy kit closed; updated 2026-09-01, when the tree froze as **v1.0.0**.

---

## Why I started this at all

The idea is simple and therefore stubborn: social networks are the wrong place for people
having a hard time. Everything there works against them — likes, counters, the showcase of
success, the obligation to look fine. Therapy is not available to everyone. Emergency
services are for acute crisis, and I deliberately do not try to replace them: the product
says honestly, everywhere, "Crisis → 112/103, don't hold a chatbot."

That is how de-press was born — a non-profit "quiet harbor." Its rules I formulated at the
very beginning and have never reworked since:

- **a monologue without comments or likes** — you write, and that's it; this is not a post chasing reach;
- **silent empathy** — instead of a like, a listener sends "I hear you," with no public counters or lists;
- **dialogue only with the author's consent** — nobody can write to a person first without their "yes";
- **support clouds are private** — support is visible only to the author, and even then as a quiet gesture on their feed row, not as an announcement;
- **Anti-Panic** — the "I'M NOT OK" button that dims the interface: WebSockets die, polling stops, only breathing and grounding remain;
- **AI without toxic positivity** — always labeled, validates feelings, never diagnoses;
- **personal mood notes stay on the device** (IndexedDB); the server never sees them.

The last point is not a setting for me, it is architecture: no server-side "trauma map"
exists even in theory.

---

## Where it began (everything before git)

The project is older than its repository. The first commit is called "chore: initialize git
for Help Request work" — I introduced git not "to start a project" but to start one concrete
feature, `/help`. That first commit swallowed 666 files and about 77 thousand lines of
already-working code in one piece.

I did not keep exact dates for that period — I started the journal (`PROGRESS.md`) later,
and the versions live in the roadmap. From them the picture is:

- **v0.0–v0.7** — the foundation: the domain, monologues, dialogues, Anti-Panic, AI, patterns on the device. The stack formed then and was never abandoned: Django + Ninja + Channels, Postgres, Redis; a monorepo.
- **v0.9** — quiet phrases and private support clouds.
- **v0.10** — the listener list and "the author can write first to those who heard them."
- **v0.11** — free text in the clouds, but only through a Helper's moderation; the Helper role, the queue.
- **v0.12–v0.13** — the design pass and ru/en bilingualism.
- **v0.14** — voice notes in dialogues with a configurable retention period.
- Plus the closed P1 "soft-notify": private notifications, digests, magic-token inbox entry without a password.

From the first days I had a habit that saved me many times: writing down every serious
decision as a separate ADR. There are twenty-two of them by now — and it is precisely by
them that you can see how much I cancelled (more on that below).

---

## The first frontend and the rewrite from scratch

My first frontend was Next.js. Then I understood that I did not need SSR at all: the product
is an app, not a site, response speed matters more than server rendering, and Next's
complexity brought more cost than benefit. I rewrote everything as a pure SPA:
**Vite + React + TypeScript + CSS Modules**.

I did not rewrite "into a drawer" but against the DESIGN_V2 spec with hard axioms, the main
one being: **Telegram ergonomics, one to one**. Three panels on desktop, a tab bar on the
phone, familiar patterns — because a person in a bad state must not have to learn my
interface. The form is Telegram's; the light and the vibe are ours: the dark theme is the
base, the light one ("dawn") is mandatory, the accent is the mint "hope." I laid out the
token architecture from day one so that themes could be added without refactoring.

I did not delete the old Next.js but moved it to `_archive/legacy/next-frontend/` — for a
long time it remained a donor of logic and types.

---

## The platform odyssey, or how I forked Telegram

The longest series of cancellations in the project is the platform one. The "four hosts"
scheme (browser, Telegram Mini App, own desktop, own mobile) is fixed in ADR 0013 and is
alive to this day. But the road to it was winding.

First I decided to build **my own native desktop** on top of tdesktop (ADR 0015), then **my
own Android** by forking Telegram for Android (ADR 0016). I really took the fork and
wrestled with it until I admitted the obvious: maintaining somebody's giant codebase with my
own forces was not going to happen, and meanwhile the product stood still. Both forks lie in
`_archive/native/` — not deleted, but not part of the product either.

The outcome turned out well:

- **The Mini App** — a full host inside Telegram, based on their Web client (ADR 0014): login via `initData`, the theme is bridged into my tokens, and dialogues and monologues still live on my backend — Telegram is only a showcase, not transport.
- **Own mobile** — this is a PWA (ADR 0019): installs to the home screen, works as an offline shell, no stores and no forks.
- **Own desktop** — Tauri over the same UI Core, honestly deferred and without guilt.

A separate decision I am proud of: **the landing and the app are two independent
repositories** with their own stacks, connected by exactly one link. Everything that is
"about the project" (guides, help, rules) goes to the landing; the app stays an app.

---

## Git, two agents, and one mad day

On August 29, 2026 I initialized git and made 14 commits of the `/help` feature: the Help
Request model, the queue with skip, accept opens a dialogue immediately, REST, the client,
bilingualism, the waiting screen, the "quiet companion" screen (`/help/ai`) — and the Helper
accepting requests from their side of the chat.

Then happened the thing that makes this project unlike my previous ones: I wrote
**MAINPLAN** — a contract for two AI agents working in parallel. One ran the
helper-operations branch: reports in the help chat, checking dialogue requests before the
author sees them, invite-only helper onboarding (one-time invitations, no open signup), the
`/helper` dashboard, the on-duty toggle, instant matching with a duty helper by heartbeat.
The other ran the AI companion and the hosts: SSE streaming with an honest offline mode,
companion memory in IndexedDB with a full-wipe button, `/help` parity in the Mini App, the
voice pipeline, the platform ADRs.

The discipline was strict — file zones, a shared journal `PROGRESS.md` with "started/done"
entries, API contracts fixed before the second agent started using them. There were
curiosities too: the agents worked in one worktree, and once the second, while switching
branches, stashed the first agent's unfinished journal entry — it later had to be fished out
of a stash. But both branches merged into `main` almost without conflicts: the only real
conflict was in `PROGRESS.md`, and it trivially concatenated.

By the evening of that same day both tracks lay in `main` in full. And then I started
rolling things back.

---

## The two big rollbacks of that same evening

I made both decisions the same evening and regret neither.

**1. Rolling back the pre-moderation of dialogue requests.** The logic was beautiful and
"safe": a Helper first reviews a dialogue request, and only then the author sees it ("we
checked — it's safe for you"). In practice it put one more gate between two people. Worse:
if nobody was on duty, the request just hung there. I rolled the feature back — requests now
go to the author directly. I made a migration `awaiting_helper → pending`, removed the
review UI from both clients, and deliberately kept the old API endpoints so old
notifications and data would not break. Reports and blocks stayed — moderation remained
post-factum.

**2. Rolling back the STT → translate → TTS voice pipeline.** It was my dream of "real
multilingualism": a depressed Japanese speaker talks with a Kyrgyz speaker, the Kyrgyz with a
French speaker — the server recognizes the speech, translates, speaks it aloud. The pipeline
was assembled in one pass: "Transcribe" and "Listen to the translation" buttons in the Mini
App, a speech endpoint, an honest 503 when the server has no key. Then I looked at it
through the eyes of a user without API keys: without keys this is not "multilingualism," it
is a set of stubs. I rolled it all back: auto-transcription on send, the buttons, the
adapters, the settings. Text-message translation stayed (it handles offline with an honest
marker too), and the transcript fields stayed in the DB — together with the old data. The
roadmap now says it plainly: "dropped: not feasible adequately without keys."

---

## Small cancellations I also count as decisions

The big rollbacks are loud, but the real product culture is made of quiet "no"s:

- **Support rays.** There was an idea of a public "send a ray" action on an entry. Threw it
  out of the UI entirely (ADR 0018), left the API alive — the data is not lost, but there
  will be no reaction showcase.
- **Clouds as a list.** First I thought: the author opens the entry page and looks at the
  clouds. Then I understood this turns support into a counter. Now a cloud is a **gesture on
  the author's own feed row** (the last unread quiet phrase); opening the monologue sends
  the gesture. No lists, no bells (ADR 0017, which reversed part of ADR 0008 — and that is
  fine; that is what ADRs are for).
- **`/help` is a gate only.** I had managed to assemble everything on the help page: crisis
  guidance, regional resources, safety paragraphs, guides. Then I cut it to two halves —
  "AI" and "a live person" — because a person in an acute state needs two buttons, not a
  library. The public pages (guides, help) moved to the landing repository.
- **UI dictionaries are not "multilingual."** I refused on principle to call the ru/en
  string catalogs a translation and pass it off as multilingualism: it is a catalog of
  strings, no more. (Later, in the pre-launch week, real dynamic translation did ship — see
  below.)
- **Docker.** Did not go for it: system Postgres and Redis, deploy to a bare VPS via
  systemd. Fewer layers — less magic to debug at three in the morning.
- **AngelSlim** (a clone of an LLM-compression toolkit) — downloaded it, looked at it, does
  not import as code. Let it lie in the archive.
- **The Helper dashboard design** — "that's for later." I said exactly that to myself and
  wrote it into the journal. (That "later" arrived the following week — see below.)

---

## The pre-launch week (August 30–31)

After the deploy kit closed, I did what I had been postponing: prepared the project for
other people's eyes.

**The docs went English.** Every document — the README, CONTEXT, MAINPLAN, PROGRESS, the
design specs, all twenty-two ADRs — was translated, and the Russian originals were archived
in `docs-ru-archive/` instead of being deleted. Old Russian journal entries stayed as they
were; new ones are written in English.

**An honest i18n engine.** Instead of the rejected dictionary approach — real dynamic
translation: a local Hunyuan-MT-7B model via Ollama on the server, per-catalog caching,
rate limits, and a browser-side fallback through Chrome's built-in Translator API when the
server has no model. Untranslated UI always shows an honest "unavailable" marker; dates
follow the UI locale everywhere.

**Privacy hardened.** No raw IPs anywhere: rate limiting switched to salted hashes, nginx
logs anonymized, and the whole data inventory written down in `PRIVACY.md` — what we store,
for how long, and why.

**The fund, the calls, the therapist.** Three contours landed as ADRs and code:

- **ADR-0020, a non-custodial fund** — tip wallets live in the user's own wallet, the server
  stores only an address; phase two added an off-chain ed25519 proof of wallet ownership and
  a "verified" badge.
- **ADR-0021, live voice** — 1:1 WebRTC calls in dialogues: signaling over the existing
  Channels WebSocket, media does not pass through the server.
- **ADR-0022, the therapist contour** — sessions with Solana Pay and manual confirmation;
  the therapist is a role, not a marketplace.

Each of the three reached parity in the Mini App the same week: feed, help, helper
operations, fund, calls, therapy.

**The Helper dashboard** — the one I had put off — shipped as a live queue over the existing
WebSocket plus duty metrics on `/helper`.

**The admin console.** A staff-facing moderation dashboard: reports, the audit log, the
dialogue-request and help queues — a separate `apps/admin` console served at `/console`.

**Retests.** After each push of scope the whole suite reran: by the last pass — backend 256
pytest tests green (run in SQLite chunks; one env nuance for the AI offline stubs), browser
69 vitest tests across 11 files, all three frontends building clean, `makemigrations
--check` clean.

---

## The last cut before the freeze

Two more changes landed right before v1, both in the "remove, not add" spirit:

**The notifications tab is gone.** From both clients: the route, the pane, the unread
polling, the soft badge, the bell icon, the i18n keys. The reasoning: private notifications
are useful, but a dedicated tab mimicking a social network's inbox is not — toasts in the
Shell, the email digest, and the bot's soft-notify deep links (now landing on `/feed`, so
old Telegram links do not 404) cover it. The backend API and `telegram_notify.py` are
touched nowhere; the dead client methods and hooks were pruned in the same pass, and the
Django admin was anglicized ("Operations") with the missing models registered as view-only
admins on a shared `ReadOnlyAdmin` base.

**Bug reports.** The inverse of the cut: a small pipeline so a pilot user who hits a problem
can say so — `POST /api/v1/bugs` (no login; an anonymous session is minted when needed), a
form in the More pane, and a triage inbox in the admin. Validated, rate-limited to 10 per
hour, 5–4000 characters.

Also restored: `/help` went back inside the navigation Shell instead of a special
full-bleed layout — one geometry for every pane.

---

## Where the project stands now (September 1, 2026) — v1.0.0

- **Eighty commits** since git init, **one branch** (`main`), the tree tagged **v1.0.0**;
  the old feature branches are deleted (all were fully merged), the two-agent stashes are
  kept as artifacts. Hotfixes, if any, branch from the tag.
- **The product core is whole**: monologues, silent empathy, private clouds, consent-only
  dialogues, circles (video purged on close), voice notes with retention settings, live
  WebRTC calls, Anti-Panic, the Helper contour, the therapist contour, the non-custodial
  fund, private notifications, the admin console, bug reports.
- **Two clients + backend**: the browser app (a PWA) and the Telegram Mini App, both at
  parity with the API, both building as version 1.0.0.
- **Tests**: backend 256 pytest tests green; browser 69 vitest tests; `tsc -b` and `vite
  build` green for every frontend; `manage.py check` and `makemigrations --check` clean.
- **The deploy kit is ready**: systemd units (API on daphne, celery, beat, a daily backup),
  nginx with same-origin proxying and privacy-safe logs, a production env example, and the
  [`DEPLOY.md`](./app/DEPLOY.md) runbook. The units passed `systemd-analyze verify`.
- **Next**: the live VPS by the runbook, a closed pilot cohort, and manual device QA (PWA
  install, offline, safe areas). The full AI helper stays in the very last queue: the quiet
  companion exists, but a "helper product" must not appear before live people and rules
  exist around it.

---

## The annals of cancellations (brief)

| Decision | What happened | Replaced by |
|---|---|---|
| Next.js frontend | rewritten from scratch | Vite + React SPA (UI Core v2) |
| Own tdesktop (ADR 0015) | fork archived | Mini App + PWA + Tauri (deferred) |
| Telegram Android fork (ADR 0016) | fork archived | Mini App + PWA |
| Support rays in the UI (ADR 0018) | removed from the UI | quiet phrases and clouds |
| Clouds as a list for the author (part of ADR 0008) | reversed by ADR 0017 | a gesture on the author's feed row |
| Pre-moderation of dialogue requests (A2) | rolled back the same day | requests go straight to the author; moderation is post-factum |
| Voice pipeline STT → translate → TTS (B3) | rolled back the same day | text translation; transcript fields kept in the DB |
| "Multilingual" via UI dictionaries | rejected as a term-substitution | real dynamic translation later (Hunyuan-MT + a browser fallback) |
| Public help and guides pages | cut from `/help`, left the app | the landing repository |
| Docker for deployment | rejected | systemd + nginx on a bare VPS |
| Open Helper registration | never built | one-time invites + a pledge |
| Native STT/TTS multilingual | dropped (not feasible without keys) | honest text translation with offline markers |
| The notifications tab | cut from both clients before v1 | Shell toasts, the email digest, bot deep links → `/feed`; the API stays |

---

## What I have left with me (instead of conclusions)

- Cut features as decisively as you add them. The two biggest rollbacks happened on a day
  when the features were done and tested — and both times the product got better.
- An honest offline beats a beautiful fake. A 503 "TTS offline: no key on server" is more
  honest than a synthetic voice pretending everything works.
- Privacy is architecture, not a checkbox in settings.
- Write decisions down (ADRs) and keep a journal. Rolling back is cheaper when there is
  something to roll back to: a git commit, a migration, a PROGRESS entry — and nothing is
  lost.
- Freezing is also a decision: one branch, a tag, and the discipline to ship fixes as
  hotfixes instead of reopening the trunk.
- And the main thing: this is a product for people who feel bad right now. Every "no" in
  this list is really a "no" to something that could hurt exactly them: the showcase, the
  counters, the gates, the fakes.
