# Native Android first (desktop build deferred)

## Status

Accepted (2026-08). **Amends** ADR 0015 priority order.

## Context

Native **tdesktop** Docker build exceeds available workstation capacity (RAM ~14 GB, disk pressure, editor crashes). Product still requires a **real Telegram native UI**, not Web A / Mini App shell.

## Decision

1. **Primary experiment track: Android** — fork of official open-source Telegram Android ([DrKLO/Telegram](https://github.com/DrKLO/Telegram) / TelegramMessenger builds).
2. **Desktop (tdesktop)** remains a valid long-term target under `native/desktop/` but is **paused** (no further Docker prepare/build until stronger machine / CI).
3. **iOS** — after Android proof (needs Mac).
4. **Web A / Mini App** — still not product “Telegram shell”.
5. **apps/browser** — independent web client, unchanged.
6. Same product injection: **de-press section** inside real Telegram UI → de-press Django API for haven features; MTProto for normal Telegram.

## First milestone (Android)

1. Clone Telegram-Android into `native/android/Telegram` (gitignored bulk).
2. Configure `API_ID` / `API_HASH` (reuse my.telegram.org credentials; platform can stay Desktop app record or create Android-named app — same keys work for client builds).
3. Build debug APK (Android Studio / Gradle / SDK).
4. Inject de-press entry + feed panel (Java/Kotlin UI + HTTP to backend).

## Consequences

- Developer needs **Android SDK / Studio** (or Docker Android build later).
- Phone/emulator for install.
- Lighter than tdesktop Docker for many machines, but still multi-GB native NDK builds.
