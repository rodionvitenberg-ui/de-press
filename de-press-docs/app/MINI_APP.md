# Telegram Mini App — dev runbook

> Host #2 of four — see [`PLATFORMS.md`](./PLATFORMS.md).  
> Code: `apps/web/src/core/host/*`, `POST /api/v1/auth/telegram`, `apps/identity/telegram.py`.

## What works in code now

1. **Bridge** — `telegram-web-app.js` in `app/index.html`; `bootstrapTelegramHost()` (ready, expand, theme).
2. **Auth** — `POST /api/v1/auth/telegram` with `{ "init_data": "<raw initData>" }`; HMAC validate → Account by `telegram_id` → Django session.
3. **HostProvider** — on app start, if inside TG with initData → seamless login; seeds React Query `["me"]`.
4. **Anti-Panic** — disables Mini App vertical swipe-to-close when active (if API exists).
5. **Deep-link `startapp=`** — maps to in-app routes once per session (`core/host/startParam.ts`).
6. **BackButton** — `TelegramBackButton` ↔ hierarchical React Router (`/feed/:id` → `/feed`, …).
7. **Bot soft-notify** — opt-in + `immediate` pings or **`daily` digests** (Celery beat / `send_telegram_digests`).
8. **Browser host** — unchanged (no initData → no TG login); browser can still use `?startapp=` for local tests.

## Deep links (`startapp`)

Telegram:

```
https://t.me/<bot>?startapp=<param>
https://t.me/<bot>/<short_name>?startapp=<param>
```

| `startapp` param | Route / effect |
|------------------|----------------|
| `feed` / `home` | `/feed` |
| `new` / `feed_new` / `write` | `/feed/new` |
| `story_<uuid>` / `s_<uuid>` | `/feed/<uuid>` |
| `chat` / `dialogues` | `/chat` |
| `chat_<uuid>` / `d_<uuid>` | `/chat/<uuid>` |
| `notifications` / `inbox` / `notify` | `/notifications` |
| `patterns` / `mood` | `/patterns` |
| `help` / `safety` / `crisis` | `/help` |
| `helper` | `/helper` |
| `panic` / `anti_panic` / `meh` | `/help` + Anti-Panic on |

Rules: `A–Z a–z 0–9 _ -`, max **64** chars (Telegram). Applied **once** per tab session (`sessionStorage`).  
Dev without TG: open `http://127.0.0.1:5174/?startapp=chat`.

## BotFather setup

1. Create bot via [@BotFather](https://t.me/BotFather) → copy token.
2. Set env:
   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC..."
   export TELEGRAM_BOT_USERNAME="your_bot"   # without @, soft-notify deep links
   ```
3. Main Mini App URL must be **HTTPS** public URL of the Vite app (tunnel in dev).

```
/mybots → Bot → Bot Settings → Configure Mini App → Enable
URL: https://<your-tunnel>/ 
```

Or menu button: `/setmenubutton` → same HTTPS URL.

## Local dev with tunnel

```bash
# Terminal 1 — API
cd backend && source .venv/bin/activate
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_BOT_USERNAME=your_bot
daphne -b 127.0.0.1 -p 8005 config.asgi:application

# Terminal 2 — UI Core (proxies /api to :8005)
cd apps/web && npm run dev
# listens 0.0.0.0:5174

# Terminal 3 — public HTTPS (example)
cloudflared tunnel --url http://127.0.0.1:5174
# or: ngrok http 5174
```

Paste tunnel URL into BotFather Mini App settings. Open bot in Telegram → Launch.

## Identity notes

- TG-only accounts use synthetic email `tg{id}@users.de-press.local` (not a mailbox).
- Password unusable; login is Mini App / future link flows.
- Public pseudonym = first_name (or username / "guest"); **@username is not shown as feed identity by default**.
- Dialogues stay on de-press WS/API — not Bot chats.

## Tests

```bash
cd backend && source .venv/bin/activate
DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory pytest \
  apps/identity/tests/test_telegram.py \
  apps/notifications/tests/test_telegram_notify.py -q
```

## BackButton

On nested routes Telegram shows the native Back control:

| Path | Back → |
|------|--------|
| `/feed/:id`, `/feed/new` | `/feed` |
| `/chat/:id` | `/chat` |
| section roots (`/feed`, `/chat`, …) | hidden |

## Soft-notify (Bot)

1. Account must have `telegram_id` (Mini App login).
2. User enables **"Quiet Telegram reminders"** in UserMenu (`notify_telegram_opt_in`).
3. Frequency:
   - **`immediate`** — on each `notify()`, Bot message + deep-link  
     `https://t.me/<bot>?startapp=chat_<uuid>|story_…|notifications`
   - **`daily`** — batch job; one digest of unread **newer than** `telegram_digest_last_at`  
     link: `startapp=notifications`

### Daily digest run

```bash
# One-shot (cron-friendly)
python manage.py send_telegram_digests

# Or Celery worker + beat (UTC hour from TELEGRAM_DIGEST_HOUR, default 10:00)
celery -A config worker -l info
celery -A config beat -l info
```

API test (logged-in TG account): `POST /api/v1/me/notify-settings/test-telegram`

## Not in this slice (next)

- Circles/mic WebView QA matrix  
