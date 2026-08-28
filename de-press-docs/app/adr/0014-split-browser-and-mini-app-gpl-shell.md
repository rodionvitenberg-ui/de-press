# Split Browser vs Mini App; Mini App uses Telegram Web A (GPLv3)

## Status

Accepted (product requirement, 2026-08).

## Context

Product requires:

1. **Browser app** and **Telegram Mini App** to be **decisively separate** codebases
   (independent evolution of UI).
2. Mini App (mobile-first, occasionally desktop WebView) must feel like a **real
   Telegram addon**: same shell/ergonomics as Telegram, de-press colors and features.
3. Open Telegram clients exist: **Web A** (`telegram-tt`), **Web K** (`tweb`),
   **tdesktop** — all **GPLv3**.

Previous ADRs/docs forbade copying tdesktop/Web A GPL code into the shared SPA.
That is **superseded for the Mini App track only**.

## Decision

| Surface | Path | Shell strategy | License note |
|---------|------|----------------|--------------|
| **Browser** | `apps/browser/` | Own de-press UI; **no** telegram-tt imports | Stays non-GPL (as long as isolated) |
| **Mini App** | `apps/mini-app/` | Vendor **Telegram Web A** (`vendor/telegram-tt`, GPLv3); integrate de-press features into that shell | Mini App client → **GPLv3** when shipping Web A derivative |
| Backend | `backend/` | Unchanged; de-press domain API/WS | Not a derivative of Web A |

- One backend; two frontends.
- No shared UI package that imports GPL into browser.
- Shared *ideas* / OpenAPI types may be duplicated or generated; not GPL source.

## Consequences

- Folder split is mandatory; edits to browser do **not** automatically change Mini App.
- Integrating Web A is multi-sprint (build system, MTProto vs our API, theming hope/panic).
- Interim Mini App may still run de-press SPA + `Telegram.WebApp` until Web A shell is wired.
- Legal: publish Mini App source under GPLv3 when distributing modified Web A.

## Non-goals (this ADR)

- Forking tdesktop native into Mini App WebView.
- Making official Telegram load proprietary plugins (impossible).
- Putting Web A inside browser app.
