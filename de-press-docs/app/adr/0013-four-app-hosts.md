# Four App Hosts: browser, Telegram Mini App, own desktop, own mobile

de-press is **one product** with **four App Hosts** (runtime surfaces), not four separate apps:

1. **Browser** — Vite SPA at `app.` (UI Core development surface and web fallback).
2. **Telegram Mini App** — the same UI Core inside Telegram’s WebView, with Bot API for seamless auth and optional soft-notify. A full host and an important **stage**, not a substitute for own mobile/desktop.
3. **Own Desktop** — native shell around the UI Core (Tauri or Electron; toolkit chosen later).
4. **Own Mobile** — own mobile app path (PWA → native shell / stores), with Telegram-like tab-bar ergonomics.

**Shared:** UI Core (`apps/web/`), Django backend (stories, dialogue, empathy, support, notifications), domain invariants, design tokens / CSS Modules (no Tailwind).

**Not shared as transport:** Telegram is **not** the message bus for Initiated Dialogue or Safe Monologues. Dialogues and monologue content stay on the de-press API/WS. Telegram may supply host chrome, `initData` identity linking, and opt-in bot digests.

**Rejected for v1:** treating Mini App as the only mobile strategy; building a TDLib fork of Telegram as the product shell; forking tdesktop/Web A (GPLv3).

**Ergonomics:** all hosts aim for Telegram-like UX; only the Mini App host is a literal platform addon inside Telegram.

See also: [`../PLATFORMS.md`](../PLATFORMS.md), [`../DESIGN_V2.md`](../DESIGN_V2.md), [`../ROADMAP.md`](../ROADMAP.md).
