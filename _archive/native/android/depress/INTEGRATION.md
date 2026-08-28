# de-press × Telegram Android — injection map

## Goal

Inside **real Telegram Android UI**: entry to haven (feed monologue, silent empathy) → **de-press HTTP API**.

## Likely hook points (after clone)

Explore under `Telegram/TMessagesProj/src/main/java/org/telegram/`:

| Area | Typical classes | Use |
|------|-----------------|-----|
| Drawer / side menu | `ui/LaunchActivity`, drawer adapters | Add “de-press” menu item |
| Chat list | `ui/DialogsActivity` | Optional top row / filter |
| Custom screens | new `ui/DepressFeedActivity` (ours) | Stories list |
| Networking | new package `org.telegram.depress` or `depress/` | OkHttp/HttpURLConnection to backend |

Exact file names vary by upstream version — re-scan after `fetch_telegram_android.sh`.

## v0 slice

1. Menu item → open feed activity.  
2. `GET {base}/api/v1/stories`  
3. Tap → story detail + empathy `POST …/empathy`  
4. `base` default: emulator `http://10.0.2.2:8005`, device LAN IP.

## Auth v0

Email/password → `/api/v1/auth/login`, store session cookie.  
Telegram MTProto login remains for normal chats.
