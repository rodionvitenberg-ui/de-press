# Design V2 — de-press.co

> The design spec of version 2.0. A living document: we discuss, fix, refine.
> Related to: `CONTEXT.md` (the domain), `FRONTEND_PLAN.md` (the engineering plan), `ROADMAP.md`.

---

## 1. Axioms (not subject to revision without a separate decision)

1. **TG ergonomics — one to one.** The interface must function the same way as the current Telegram:
   - the desktop version (a 3-pane layout);
   - the mobile version (a bottom tab bar / nested screens).
   We take Telegram's ergonomics to the maximum: it fits the project's goals. This is the main statement of the design.
2. **Recognition + vibe = 50/50.** The familiarity of the TG patterns and our own "quiet warm" atmosphere in equal measure.
   - The TG design is "borrowed" where it is ergonomics/layout (axiom 1);
   - our own product functions get our own solutions (see §5).
3. **Multi-theming — an imperative.**
   - The dark theme is the base one (current);
   - the light theme ("dawn") is mandatory in v2.0;
   - named themes live in `@de-press/theme`; the token architecture must support further themes without a refactor;
   - a theme switcher is needed: Auto plus every named id from the registry (not only auto / dark / light); no hardcoded colors in the components.
4. **The colors are ours.** The form is TG, the color/light/vibe is de-press (the mint `hope`, calm dark/light palettes).
5. **The user's screenshot is the source of truth for the screen layout** (see §5). The image is temporarily unavailable to the agent — the layout is fixed as text below and requires a confirmation.

---

## 2. Site ≠ App; the app = 4 hosts

**A hard line:** the landing page and the app are separated.  
**This repository** — apps only. The app has **four directions (App Hosts)** — see [`PLATFORMS.md`](./PLATFORMS.md) and [ADR 0013](./adr/0013-four-app-hosts.md).

### 2.1 The landing / site (marketing surface — ANOTHER REPOSITORY)
- The external, demonstrative information: the idea, the rules of use, help, "about the project", FAQ, storytelling.
- It is developed **in a separate repository**, on **its own stack** and **its own visual engine**.
- **The only connection** between the landing and the app is a **jump link** (for example `https://depress.co` → `https://app.depress.co`). That's all.
- The landing docs live in the shared folder [`de-press-docs/site/`](../site/), the code — in its repository.

### 2.2 The four App Hosts (the decision is fixed)

| # | Host | The essence |
|---|------|------|
| 1 | **Browser** | A SPA on `app.` — the UI Core, the web fallback |
| 2 | **Telegram Mini App** | The same UI Core in the Telegram WebView + a Bot — **a stage and a full host**, not a replacement for #3/#4 |
| 3 | **Own Desktop** | Our own desktop (a wrapper over the core: Tauri / Electron — choose later) |
| 4 | **Own Mobile** | Our own mobile (PWA → a native wrapper / store), the TG tab bar |

- **UI Core** (`apps/web/`): Vite + React + TypeScript + CSS Modules — one bundle/core for all hosts.
- **One backend**: Django + Ninja + Channels. Dialogues and monologues do **not** ride through MTProto/Bot chat as a transport.
- The v2 UX target: **TG ergonomics 1:1** on all hosts; on the Mini App — also literally a host inside Telegram.
- **The browser subdomain:** `app.` (for example `app.depress.co`) — fixed.
- Right now: **the Browser host** (a core prototype). The Mini App is the next interesting stage. Own mobile / own desktop — after/in parallel with a mature core.

### 2.3 Host adapters (lay down now)
- Thin adapters: browser | telegram | desktop | mobile — without the domain spreading across hosts.
- Components without a hard binding to one runtime; an isolated API layer.
- Mini App: `initData` auth, themeParams → tokens, BackButton, optional bot soft-notify.
- Own desktop/mobile: the OS shell, install, permissions — over the same core.

### 2.4 The stack (the decision is fixed)
- **The core (UI Core)**: **Vite + React + TypeScript + CSS Modules** — a pure SPA, no SSR; the maximum response speed.
- **The v2 components** (TG ergonomics); the logic/types/API/tokens are reused, not the GPL layout of tdesktop.
- **PWA** — a bridge to own mobile (P1+), **not** a cancellation of a separate mobile host.
- A shared `core/`: tokens, types, the API client, i18n, WS — for all four hosts.
- Legacy `_archive/legacy/next-frontend/` (Next.js) — not the main UI; a logic donor when needed.

---
## 3. The concept: "A warm Telegram"

Telegram gives the skeleton: three zones, lists, bubbles, search, a tab bar. de-press adds the tone:

- **Silence instead of pressure.** No showcase counters, no pulsing suffering badges, no "online". "Typing…" — we take it as in TG (§10.4), softening the text tone if needed at the implementation stage.
- **Breathing instead of haste.** Slow smooth transitions, soft entrances, no sharp animations on high-frequency actions.
- **The mint/hope accent is the only one for action.** `--accent-hope` for an action; `--accent-panic` — only crisis/destructive (`I'M NOT OK`). In `aurora` hope is `#5fc4aa` (island teal), not white: a white chrome accent from the landing would collapse action vs surface in the messenger.
- **No Tailwind.** CSS Modules + design tokens (a project rule).

---

## 4. Theming

### 4.1 The requirements (an imperative)

- All colors — only through CSS tokens (`:root` + `[data-theme="..."]`), not a single hardcode in the modules. Source of truth: `@de-press/theme` (`packages/theme` — registry + `tokens.css`); both hosts import it ([ADR 0024](./adr/0024-theme-registry.md)).
- Themes in v2.0: `dark` (current, default), `light` ("dawn"), `aurora` (opt-in). Further palettes (`sepia` / `dim` / `contrast`) are added through the registry, not a refactor.
- The switcher: Auto plus every named id from the registry (today: Auto / Dark / Light / Aurora) — in the sidebar (the user modal, see §5.2) and on the settings page.
- Auto resolves only to `dark` or `light` (OS `prefers-color-scheme` / Telegram `colorScheme`). `aurora` is never chosen by Auto.
- Every theme overrides the **entire** color token set (the background, surface, text, borders, shadows, bubbles, input/composer, on-accent). Geometry, radii, font, durations stay on `:root`.
- `media (prefers-color-scheme)` — the base auto logic; `data-theme` overrides it.
- `color-scheme: dark/light` — sync with the scrollbars/native controls.

### 4.2 The tokens for v2.0 (a starting set, extendable)

```
--bg-main / --bg-surface / --bg-elevated / --bg-sidebar / --bg-chat
--bg-input / --bg-hover / --bg-active
--bg-bubble-me / --bg-bubble-them
--text-primary / --text-muted / --text-bubble / --text-bubble-muted
--accent-hope (+ soft/mid) / --accent-panic
--on-accent-hope / --on-accent-panic
--border-subtle / --border-soft
--shadow-elev-1/2, --shadow-cloud
--radius-* (concentric, see better-ui: outer = inner + padding)
--transition-* (the durations)
```

### 4.3 The light theme — candidate values

A calm "dawn": a warm grey-beige background, a dark graphite text, bubble-me = mint (dark) on light, bubble-them = light grey. The exact values — at the implementation stage + a vibe confirmation. IMPORTANT: for mental health the light mode is often more critical than the dark one (less contrast stimulation during the day).

### 4.4 Aurora

Cinematic navy, not graphite Telegram-night: page `#0c101b`, muted text in periwinkle, hope `#5fc4aa`. Opt-in only; no light twin; Auto never selects it. Full token values live in `packages/theme/src/tokens.css` (`:root[data-theme="aurora"]`) — do not duplicate the table here.

---

## 5. The skeleton: 3 zones (desktop) / a tab bar (mobile)

The layout from the user's screenshot description (requires a confirmation):

### 5.1 The scheme (desktop)

```
┌────────────────┬─────────────────────┬──────────────────────────┐
│ PINK (nav.)    │  YELLOW (list)      │  RED (content)           │
│ ┌────────────┐ │ ┌─────────────────┐ │ ┌──────────────────────┐ │
│ │ burger     │ │ │ search          │ │ │ header / title       │ │
│ │ user modal │ │ ├─────────────────┤ │ ├──────────────────────┤ │
│ │            │ │ │ chat #1         │ │ │ content              │ │
│ ├────────────┤ │ │ chat #2 (grey)  │ │ │                      │ │
│ │ feed       │ │ │ …               │ │ │                      │ │
│ │ chat       │ │ │                 │ │ │                      │ │
│ │ help       │ │ │                 │ │ ├──────────────────────┤ │
│ │ patterns   │ │ │                 │ │ │ composer/actions     │ │
│ │ notifs     │ │ │                 │ │ │  [chat] [rays] […]   │ │
│ │ helpers*   │ │ │                 │ │ └──────────────────────┘ │
│ │ edit       │ │ └─────────────────┘ │                          │
│ ├────────────┤ │                     │                          │
│ │ I'M NOT OK │ │                     │                          │
│ └────────────┘ │                     │                          │
└────────────────┴─────────────────────┴──────────────────────────┘
* helpers — visible to Helper roles only
```

### 5.2 The pink zone — the left sidebar (navigation)

A list top-down (the buttons must have recognizable icons — see §8):

1. **Burger / User** — opens the user modal: profile, settings, themes, whatever the project needs.
2. **Feed** — the feed (monologues).
3. **Chat** — Dialogues + Dialogue Requests. (Conceptually the feed and the chat work almost the same: a list on the left, content on the right.)
4. **Help** — Help (discussed separately, §6.6).
5. **Patterns** — local (ZK).
6. **Notifications** — Notification (private).
7. **Helpers** — the Helper queue (only for users with the Helper role; otherwise hidden).
8. **Edit** — the sidebar setup mode: reorder the buttons by tap, hide/show.

At the bottom — the **always visible stop button `I'M NOT OK`** (Anti-Panic). It sharply simplifies the interface, removes all irritation sources, severs realtime, and shows the minimal grounding screen.

### 5.3 The yellow zone — the list (NV = notifications/summary)

- Always at the top — **search** (as in TG).
- **Chat**: the dialogue list + **specially styled Dialogue Requests**:
  - looks like a human in the list, but "grey";
  - the first message is not visible;
  - instead of the message — a system banner: *"The user requests a conversation with you. We checked the request — it is safe for you to accept it"*. The banner appears after manual moderation by a human with the Helper role (§10.3).
- **The feed**: in the yellow zone — new thoughts (Monologues), styled **exactly like TG chats**: the avatar/pseudonym of a participant, a 1–2 line text preview, the time. Visually the user cannot tell a "feed post" from a "chat in a messenger" — that is intentional.
- The first feed item — the **`ADD ENTRY` placeholder** (your own post): styled as a "new chat/contact", a tap opens the publishing composer.

### 5.4 The red zone — content/actions

- **Chat**: fully as in TG (the header, bubbles, time, a composer with text + microphone + send; "circles" and voice notes — by the roadmap).
- **The feed (an open thought)**: in the red zone — its own functionality. At the bottom of the section, horizontally:
  - on the left — the **Chat** button (start/continue a dialogue with the author with consent);
  - in the center — the **quiet gesture** (a Quiet Phrase), not rays;
  - on the right — an edge action (translate/report/menu `⋯` — to decide).
  - The monologue is displayed NOT as a chat but as a "thought" — a card (the domain format, §10.1), while the list in the yellow zone is TG-styled. This is the key difference between the feed and the chat.

### 5.5 Mobile

- The TG mobile pattern: a bottom tab bar + nested screens (list → detail, back). The tab bar: Feed, Chats, Notifications, More (or per the decision on the bottom 4–5 buttons).
- `I'M NOT OK` — always accessible: a floating stop button in a corner/the header + an item in "More".

---

## 6. Mapping the domain → surfaces (v2.0)

| Domain (CONTEXT.md) | Where it lives in v2.0 |
|---|---|
| **Feed** (the monologue feed) | The yellow zone — a TG list; the red zone — viewing a thought |
| **Story / Safe Monologue** | A yellow-zone item (like a chat) + a thought card in the red zone |
| **Silent Empathy** ("I hear you") | Not a separate "rays" button (ADR 0018). A cloud gesture + an optional dialogue request |
| **Support Cloud / Moderated Cloud** | The guest sends a gesture from the thought card; the author gets an animation on their own feed row, not a list and not a badge (ADR 0017) |
| **Dialogue Request** | The yellow zone of the chat — a "grey" item + the system banner "the request is safe" |
| **Initiated Dialogue** | The red zone — a TG 1:1 chat |
| **Inbox / magic token** | A separate screen (sign-in by token); outside the three zones |
| **Notification** | The "Notifications" item in the sidebar; soft badges |
| **Helper queue** | The "Helpers" item (Helper only); a separate screen |
| **Patterns (ZK)** | The "Patterns" item; a local screen |
| **Anti-Panic / "I'M NOT OK"** | The stop button at the bottom of the sidebar + a floating one on mobile; it crushes everything to the minimum |
| **Auth / Account** | The user modal (burger) |

---

## 7. Gap map: current → v2.0

| Area | Now (code) | The v2.0 target | Priority |
|---|---|---|---|
| Sidebar | `Sidebar.tsx`: 5 items + 4 at the bottom, panic at the bottom | A burger modal, all 8 items + Edit, "I'M NOT OK" at the bottom always | P0 |
| The list (yellow zone) | Absent as a single pattern; the feed is cards (`StoryCard`) | A TG list: search + chat rows; the feed placeholder "ADD ENTRY" | P0 |
| The right zone | The `main` content of pages | A header + content + bottom actions (chat/rays/…) | P0 |
| Chat | `DialogueClient` is already TG-styled (bubbles, composer) | Push to the TG details: time, 1:1 radii, states | P0 |
| Dialogue Requests | Cards on `/me` | Grey items in the yellow zone of the chat + a system banner | P0 |
| Themes | Dark only, `color-scheme: dark` | Dark + Light + Aurora + Auto (Auto → dark\|light); registry in `@de-press/theme` | P0 |
| Tokens | A base in `globals.css` | The full set (backgrounds/surfaces/bubbles/shadows), concentric radii | P0 |
| Icons | Inline SVG 1.5px in `Sidebar` | A full set, recognizable glyphs, 1.5/2px by the text weight | P1 |
| Mobile | `BottomNav` with 4 items | A TG tab bar + "I'M NOT OK", nested screens | P1 |
| Help / Patterns / Helper | Separate pages | Separate design solutions (outside the TG skeleton) | P2 |

---
## 8. Icons (P1)

For every sidebar button — a clear, recognizable glyph (by the better-ui principles: `currentColor`, outline by default, fill in the active state, 1.5px for normal text / 2px for semibold, optical alignment):

- Burger/User: an avatar/profile (or a burger)
- Feed: the "«" mark (a list/feed)
- Chat: a bubble (the current one)
- Help: a question mark / a lifebuoy
- Patterns: a wave/a chart
- Notifications: a bell
- Helpers: a shield/a hand
- Edit: "pencil/mode" (or "⋮⋮" for reordering)
- I'M NOT OK: alarming but not a "red danger button" — it is a self-care button. Visually: calm, separate, always visible.
- The red-zone actions: a dialogue request, a quiet gesture, a menu (`⋯`). No support rays (ADR 0018).

---

## 9. The implementation stages (into the task plan)

1. **P0 — Tokens and themes.** The full token set (dark+light), `data-theme`, the switcher, `color-scheme`, remove the color hardcodes.
2. **P0 — The site/app boundary + 4 hosts.** The landing is separate; the browser SPA on `app.`; lay down the host adapters (browser / Mini App / own desktop / own mobile) — see [`PLATFORMS.md`](./PLATFORMS.md).
3. **P0 — The 3-zone skeleton.** Refactoring `Shell` into 3 zones; a clean-width sidebar list (15rem), the red zone with a header and bottom actions.
4. **P0 — The yellow zone (the list).** The "chat row" pattern; search; rendering the feed as a TG list; the "ADD ENTRY" placeholder; the grey Dialogue Requests.
5. **P0 — The red zone (content).** Viewing a thought with a quiet gesture and a dialogue request; pushing the chat to the TG details.
6. **P1 — The burger modal, settings, the sidebar Edit mode.**
7. **P1 — Icons.** A single set.
8. **P1 — The Own Mobile layout.** The TG tab bar, "I'M NOT OK" in a corner, nested screens (host #4).
9. **P1 — The Telegram Mini App host.** The bridge, initData auth, themeParams; a stage, not a replacement for own mobile.
10. **P2 — Help / Patterns / Helper** — separate design briefs.
11. **P2 — Own Desktop / Own Mobile shells.** Native wrappers / PWA over the UI Core.

---

## 10. The resolution of the open questions (fixed)

1. **A monologue in the red zone — render it as a card (a "thought").** Domain: a monologue, not a message. The list in the yellow zone — TG-style.
2. **The support rays are removed from the UI (ADR 0018).** Support = a quiet gesture (a cloud) and an optional dialogue request, not a separate tap "I hear you".
3. **The Dialogue Request is checked by a human with the Helper role.** Moderation is **always manual**. The banner "we checked, it is safe for you to accept" — after the manual check by the Helper.
4. **"Typing…" — we take it as in TG.** The pattern stays (we may soften the text tone — at the implementation stage).
5. **The unread badges — soft.** No showcase of suffering, no hard screaming TG badges.
6. **Help/Patterns/Helpers — separate design briefs later**, but **in the same token system**.
7. **"I'M NOT OK" — always in the sidebar. It is a switch between modes.** The "ANTI-PANIC" mode and its display will be thought through separately.

---

## 11. The summary (what is fixed finally)

**The boundary = site ≠ app.** The landing is separate; the app = **4 hosts** (browser · Mini App · own desktop · own mobile) on one UI Core. The browser access: from the landing and a direct `app.` link. The Mini App — a stage inside Telegram. Own desktop/mobile — our own shells, not "the Mini App only".

**The form = Telegram 1:1.** Three panes (nav / list / content) on desktop, a tab bar + nesting on mobile, search in the list, bubbles, "typing…", chat rows.

**The tone = de-press.** A "thought" card for the monologue, quiet gestures without a showcase, soft badges, calm transitions, the single `hope` accent.

**Themes = mandatory multi-theming.** dark + light ("dawn") + opt-in `aurora` in v2.0, a registry for further themes (`@de-press/theme`), a switcher of Auto plus every named id (Auto never picks aurora).

**Safety = manual.** The Dialogue Request passes the Helper's check (a human), moderation is always manual.

**Anti-Panic = a mode switch.** "I'M NOT OK" is always in the sidebar; the Anti-Panic mode itself is a separate design brief.

**The implementation stages** — see §9. There are no more open questions on the design concept; the next steps are the engineering tasks from §9.

## 11.5 The app stack (fixed)
1. **The core**: Vite + React + TypeScript + CSS Modules — a pure SPA without SSR.
2. **The app URL**: the `app.` subdomain (for example `app.depress.co`).
3. **The components**: rewritten for v2 (TG ergonomics); from `_archive/legacy/next-frontend/` the logic/types/API/tokens are reused, not the layout.
4. **The `core/` layer**: tokens, types, the API client, i18n, WS — shared by all 4 hosts; thin host adapters.
5. **PWA** (offline/installable) — P1, a bridge to own mobile; the Mini App — a separate host/stage.
6. **The speed measurement**: a baseline TTI/transitions before and after the refactor — a mandatory P0 acceptance criterion.
7. **Data/state**: TanStack Query (a cache) + a light state; list virtualization (`@tanstack/react-virtual`) for the TG feed/chats; the TS types generated from the OpenAPI of Django.
