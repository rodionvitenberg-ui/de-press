# Open questions — August 2026

Collected before the "parity + helper dashboard + docs translation + retest" phase — see [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md). Format: question → options → recommendation → status. The decisions are fixed 2026-08-30 (all 10 answered; the summary is in [ROADMAP.md](./ROADMAP.md), the "Phase decisions" section).

## Q1. Who has access to voice/video

Question: should live voice (ADR 0021) and circles (video) be available to all users to talk to each other, or only in a conversation with a helper/therapist?

- **A. Status quo:** voice and video live inside the 1:1 dialogue, the role does not matter (with each other — yes; helper/therapist — the same dialogues).
- **B. Only with a helper/therapist:** a role gate in the signaling consumers and the UI.
- **C. Open groups/rooms** — not doing (ROADMAP "Not doing").

**Recommendation: A.** Both participants are already in the dialogue (consent exists), the call is declineable, there is busy and the anti-panic kill; peer support "human to human" is the core of the product — restricting it by role kills the point; the therapist gets the same mechanism with no special code. Circles are ephemeral (deleted when the chat closes).
Status: ✅ resolved (2026-08-30): A — the status quo is confirmed.

## Q2. Calls in the Mini App

Question: should `call.*` (live voice) be ported to the Mini App now?

Context: WebRTC in the TG webview behaves differently across clients; the signaling over the dialogue WS is already ready; it can only be really tested on devices in the pilot.

**Recommendation:** defer until the pilot, do not block in the code (later — feature-detect `navigator.mediaDevices`). Text and voice notes already exist in the Mini App.
Status: ✅ resolved (2026-08-30): we port them to the Mini App — the work is added to the plan (P1.3).

## Q3. What "an open dashboard" of a helper means

- **A.** A tab in the left panel, visible to helpers only (`is_helper`), with transparent queue statistics inside.
- **B.** A public transparency page for everyone.

**Recommendation: A now** (`/helper` already exists and is hidden from non-helpers — we evolve it into the dashboard), **B later** as a separate aggregated page without PII.
Status: ✅ resolved (2026-08-30): A.

## Q4. Dashboard realtime: WS or polling

**Recommendation:** v1 — polling (react-query `refetchInterval` 15–30s, as in the existing panels); a WS queue channel — only if the pilot shows the lag hurts. YAGNI.
Status: ✅ resolved (2026-08-30): a WS queue channel from the start, no polling.

## Q5. Repository preparation

Sub-questions: publish to GitHub (private/public)? A license (recommendation: **AGPL-3.0** — self-hosting + protection from cloud clones)? Clean the git history (the author's email)? CI (GitHub Actions: ruff + pytest in chunks, vitest, both vite builds)?

**Recommendation:** private → public after the retest; AGPL-3.0; do not rewrite the history, but check `git log --format=%ae | sort -u`; a minimal CI — at publication.
Status: ✅ resolved (2026-08-30): the GitHub publication is the last task of the whole project (after everything else is closed); license/CI/README — at the moment of publication.

## Q6. Docs translation: EN instead of RU or bilingual?

- **A.** EN becomes canon, the RU versions are removed.
- **B.** Keep both languages (a double edit on every change).

**Recommendation: A.** Fix the glossary before the translation (the pairs live in [GLOSSARY.md](./GLOSSARY.md): хелпер → helper, облако → support cloud, тихие фразы → quiet phrases, «мне хуёво» → "I'm not ok", кружочки → video circles, etc.).
Status: ✅ resolved (2026-08-30): A — EN canon; the RU versions are copied to `docs-ru-archive/` at the project root (the folder is in .gitignore).

## Q7. A user calling a helper directly

Question: can a user initiate a call to a helper directly, outside a dialogue?

**Recommendation: no.** The call stays inside the dialogue (a declineable "ring", busy, anti-panic; no cold calls). A conversation with a helper starts via a help request/a cloud — that already works.
Status: ✅ resolved (2026-08-30): no, the recommendation is accepted.

## Q8. Which metrics are ethical for the dashboard

**Proposal:** the queue length, the median waiting time, the number of taken/closed requests per period, who is on duty. **NO:** per-helper response time in seconds, ratings, "productivity", any engagement metrics (the ADR 0017 invariant).
Status: ✅ resolved (2026-08-30): accepted.

## Q9. The depth of the full retest

- **A.** A manual checklist per the PILOT.md smoke, extended to all features.
- **B.** Playwright E2E on top.

**Recommendation: A now** (a faster path to manual QA), B — after the pilot, when the scenarios settle.
Status: ✅ resolved (2026-08-30): A — a manual checklist.

## Q10. Anonymous therapy clients

Currently an anonymous user (without an account) can request a paid session (the backend allows it). Keep it for the pilot?

**Recommendation: keep** (privacy-first, the payment is off-platform); we monitor spam in the pilot.
Status: ✅ resolved (2026-08-30): we keep it. The principle: an anonymous user has the same capabilities as a registered one; **all history always lives in the user's browser, not with us**.

## Q11. The admin panel: the tech and the place

**Decision (2026-08-31, owner):** a separate Vite app (`apps/admin`), not a staff route inside the browser SPA — a foundation for several future admins; the admin code is not shipped to the regular users. The moderation actions require `is_staff`/superuser; the helpers keep the view-only reports visibility in their dashboard.
Status: ✅ resolved.

## Q12. What the admin may see (the privacy frame)

**Decision (2026-08-31):** the aggregates only (the visitors/the posts — counts, never identities, no IPs/fingerprints); the moderation sees only the reported item, the removal reason is mandatory, every action lands in the `ModerationAction` audit log; the default action is a reversible hide, the removal is exceptional; no reading of the dialogues, no browsing of others' content.
Status: ✅ resolved (the invariants for the implementation).
