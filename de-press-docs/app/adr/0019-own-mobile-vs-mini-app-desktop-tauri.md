# Own mobile vs Mini App, and own desktop shell = Tauri (deferred)

## Status

Accepted (2026-08). Amends the scope boundary of ADR 0014; coexists with ADR 0015/0016 (those cover the **Telegram-native fork** track — a different product goal from the **own de-press client** below).

## Context

Two questions kept getting conflated:

1. **Is the Telegram Mini App our "own mobile" client?** No. The Mini App runs inside Telegram's WebView (session, chrome, lifecycle and push all belong to Telegram). It is an *addon*, and Track B keeps it at HELP parity for that role. An **own mobile** client must work without Telegram: installed on the home screen, own push, own store presence.
2. **What is our own desktop shell?** Not the tdesktop fork (ADR 0015/0016 — that is the "real Telegram UI" track and is paused/Android-first due to machine limits). The own desktop client is a thin shell around the **existing browser build**.

Facts today: `apps/browser` is already an installable **PWA** (`manifest.webmanifest` + `sw.js`, registered in prod). No `native/` code exists yet, and none is required by this decision.

## Decision

1. **Mini App ≠ own mobile.** The Mini App stays a Telegram addon (HELP parity done in Track B). It never becomes the primary mobile client, and we do not count it when saying "we have own mobile".
2. **Own mobile = PWA-first.** The installable PWA is the own-mobile path. Missing pieces to call it complete (backlog, **no code now**):
   - **Web Push** — VAPID keys, push subscription storage on backend, permission prompt UX (silenced in Anti-Panic by design);
   - **Store chrome** — optional TWA/Bubblewrap wrapper for Play Store listing, only if distribution requires it;
   - background sync / badge polish on mobile WebViews.
3. **Own desktop shell = Tauri** (WebView wrapper reusing the browser build as-is; no fork, no second UI). **Deferred**: same workstation constraints that paused the tdesktop build (ADR 0016) apply; revisit when RAM/disk/CI budget exists. Rejected alternative: Electron (heavier than needed for a thin shell).
4. The `native/` directory is reserved for **agent B only**. It stays empty until the Tauri experiment actually starts — this ADR deliberately ships **no native code**.

## Consequences

- "Own mobile" progress is measured by the PWA checklist above, not by Mini App features.
- Backend will need a push-subscription model + VAPD endpoint before own mobile can be called complete (separate task, contract to be claimed in PROGRESS).
- Tauri start will be a small `native/desktop/` scaffold loading the browser build — no product code duplicated.

## Non-goals

- Publishing to app stores now; shipping any native code now.
- Using the Mini App as evidence of "own mobile".
- Touching the Telegram-fork track (ADR 0015/0016) from Track B.
