# GPL notice — Telegram shell vendor

`apps/mini-app/vendor/telegram-tt/` is a shallow clone of **Telegram Web A**
([Ajaxy/telegram-tt](https://github.com/Ajaxy/telegram-tt)), licensed under **GNU GPL v3**.

## Repository hygiene

- The vendor directory is **gitignored and never committed**. The published de-press
  repository contains **no GPL code**; it is licensed as a whole under AGPL-3.0-or-later
  (see the root `LICENSE`).
- `scripts/fetch_telegram_tt.sh` fetches the vendor at a **pinned upstream revision**
  so a Mini App build always maps to one known Web A source tree (reproducible
  Corresponding Source).
- Today the Mini App `src/` is an interim SPA and does **not** import the vendor yet.
  The obligations below start applying the moment a shipped build links or derives Web A.

## Product decision (2026-08)

de-press Mini App will use the **actual Telegram Web A UI/shell** as the host chrome
and interaction model so the product feels like a native Telegram addon
(same lists, bubbles, density; de-press colors/actions layered on top).

## Copyleft obligations

If we **link/modify and distribute** code derived from telegram-tt:

1. The **Mini App client** (and any combined work that is a derivative of Web A)
   must be available under **GPLv3** (or compatible) with corresponding source.
2. The **browser app** (`apps/browser/`) stays a **separate program** and must **not**
   import or bundle GPL vendor code — keep process/folder isolation.
3. Backend (`backend/`) remains separate; talk over HTTP/WS only.

This is intentional: Mini App track accepts GPLv3; browser track does not pull Web A.
AGPL-3.0 (the repo license) and GPLv3 are compatible to combine (GPLv3 §13); the
combined Mini App is shipped with this repository plus the pinned upstream as source.

## Do not

- Copy files from `vendor/telegram-tt` into `apps/browser/`.
- Relicense Web A as proprietary.
- Ship a binary-only Mini App without source.
- Unpin the vendor revision in `scripts/fetch_telegram_tt.sh` without updating this file.

See ADR `de-press-docs/app/adr/0014-split-browser-and-mini-app-gpl-shell.md`.
