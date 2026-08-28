# Native Telegram shell: tdesktop first, then native mobile (no Web shell)

## Status

Accepted (2026-08). Supersedes product intent of ADR 0014 regarding **Web A as the product chrome**.

## Context

Product requires de-press to feel like an **addon inside real Telegram**: same native UI, de-press features layered in.

Open clients:

| Client | Use for de-press shell |
|--------|-------------------------|
| **tdesktop** (C++/Qt, GPLv3) | **Yes — primary desktop** |
| **Telegram-Android / Telegram-iOS** | **Yes — native mobile (after desktop proof)** |
| Web A / Web K / Mini App WebView | **No** as the product “Telegram shell” |

## Decision

1. **Desktop shell** = fork of [telegramdesktop/tdesktop](https://github.com/telegramdesktop/tdesktop) under `native/desktop/`.
2. **Mobile shell** = native Android/iOS Telegram forks later (`native/android`, `native/ios`) — not Mini App.
3. **de-press backend** remains Django API/WS; haven data does **not** use MTProto as transport.
4. **apps/browser** stays independent web UI (no tdesktop code).
5. **apps/mini-app** and **vendor/telegram-tt** are not the path for “real Telegram UI”; do not invest in Web A as shell.
6. Distributed desktop client derived from tdesktop is **GPLv3**; keep browser free of that linkage.

## Consequences

- Build cost is high (Docker Linux build, disk, RAM, API_ID/API_HASH).
- UI work is C++/Qt, not React.
- First milestone: vanilla fork runs + de-press section + feed from API.

## Non-goals

- Embedding Web A into desktop as the official shell.
- Replacing Telegram private chats with de-press monologues.
