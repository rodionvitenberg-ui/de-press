# de-press Android — fork of Telegram Android

**Primary native experiment** (desktop tdesktop paused — ADR 0016).

| | |
|--|--|
| Upstream | https://github.com/DrKLO/Telegram |
| License | GPL (publish source when distributing) |
| Clone | `Telegram/` via `./scripts/fetch_telegram_android.sh` |
| Keys | same `api_id` / `api_hash` from my.telegram.org → `local.properties` |

## Layout

```
native/android/
  README.md
  NOTICE.GPL.md
  docs/BUILD.md
  scripts/fetch_telegram_android.sh
  depress/                 # our Java/Kotlin glue (grows)
  Telegram/                # upstream clone (gitignored)
```

## Goal

Real **Telegram Android UI** + section **de-press** (stories / silent empathy / later dialogue) talking to **our** backend — not a WebView Mini App as the shell.

## Quick start

1. Install **Android Studio** + SDK + NDK (see `docs/BUILD.md`).
2. `./scripts/fetch_telegram_android.sh`
3. Put keys into `Telegram/local.properties` (script helps from `native/desktop/.env` or `native/android/.env`).
4. Open `Telegram/` in Android Studio → Build debug APK.
5. After vanilla app runs → inject de-press UI (`depress/INTEGRATION.md`).

## Desktop

`../desktop/` kept for later; do not run Docker tdesktop prepare on this machine for now.
