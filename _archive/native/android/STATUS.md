# Android track — status

## Done

- [x] Desktop tdesktop track **paused** (capacity)
- [x] ADR 0016 Android-first
- [x] Scaffold `native/android/`
- [x] Clone DrKLO/Telegram (~903 MB)
- [x] Patch `BuildVars.java` APP_ID / APP_HASH from desktop `.env`
- [x] `SUPPORTS_PASSKEYS = false` (fork)

## Blocked on this machine until

- [ ] **Android Studio + SDK 35 + NDK 27.2** installed
- [ ] JDK 17 available (`java` not found earlier)
- [ ] `Telegram/local.properties` with `sdk.dir=…`
- [ ] First Gradle debug build / install on device or emulator

## Next after SDK

1. Open `native/android/Telegram` in Android Studio (Open, not Import).  
2. Sync + Run `TMessagesProj_App` / standalone debug.  
3. Inject de-press menu + feed (`depress/INTEGRATION.md`).
