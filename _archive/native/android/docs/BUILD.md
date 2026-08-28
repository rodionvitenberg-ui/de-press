# Build Telegram Android (de-press fork base)

Upstream: [DrKLO/Telegram](https://github.com/DrKLO/Telegram)

## Requirements

- **Android Studio** (Giraffe+ recommended) or command-line SDK
- Android SDK + **NDK** (version as required by project’s `build.gradle` / docs)
- JDK 17 (typical)
- Free disk: **≥15–25 GB** for clone + builds (lighter than tdesktop Docker, still large)
- Phone or emulator
- `api_id` + `api_hash` from [my.telegram.org](https://my.telegram.org)

## Clone

```bash
cd native/android
./scripts/fetch_telegram_android.sh
```

## Configure API keys

Upstream expects keys in:

`Telegram/TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java`

```java
public static int APP_ID = …;
public static String APP_HASH = "…";
```

We patch these from `native/desktop/.env` (already done if you used our scripts).  
Also set `local.properties` with SDK path:

```bash
# after installing Android Studio SDK:
echo "sdk.dir=$HOME/Android/Sdk" > Telegram/local.properties
```

**This machine currently may have no Android SDK / Java** — install **Android Studio 2025.1+**, SDK **35**, NDK **27.2.12479018** (upstream README).

## Build

**Android Studio:** Open `native/android/Telegram` → Sync → Run `TMessagesProj` debug.

**CLI** (after SDK configured):

```bash
cd Telegram
./gradlew :TMessagesProj:assembleAfatDebug
# APK path printed by Gradle (often TMessagesProj/build/outputs/apk/...)
```

## de-press backend while testing

```bash
cd backend && source .venv/bin/activate
daphne -b 0.0.0.0 -p 8005 config.asgi:application
# emulator: 10.0.2.2:8005 → host machine
# physical device: your LAN IP:8005
```

## Notes

- First native NDK build is long; later builds are incremental.
- If this machine still struggles, use a cloud CI Android builder later — still better than tdesktop Docker here.
