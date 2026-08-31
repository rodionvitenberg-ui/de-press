# de-press.co

A non-profit, empathetic "quiet harbor" platform for people having a hard time:

**monologues without likes** · **silent empathy** · **dialogue only with the author's consent** · **Anti-Panic** · **AI without toxic positivity** · **patterns stay on the device**.

| Document | Purpose |
|----------|---------|
| [`de-press-docs/`](./de-press-docs/) | **Single documentation** (app + site) |
| [`de-press-docs/HISTORY.md`](./de-press-docs/HISTORY.md) | **Development history** — how it was built, every rollback, v1.0.0 |
| [`CONTEXT.md`](./CONTEXT.md) | Domain vocabulary (terms) |
| [`de-press-docs/app/PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md) | **4 hosts**: browser · Mini App · desktop · mobile |
| [`de-press-docs/app/`](./de-press-docs/app/) | Design, roadmap, ADR, pilot |
| [`de-press-docs/app/DESIGN_V2.md`](./de-press-docs/app/DESIGN_V2.md) | TG skeleton, themes, axioms |
| [`de-press-docs/app/TG_SHELL_SPEC.md`](./de-press-docs/app/TG_SHELL_SPEC.md) | Shell geometry "like Telegram Desktop" |
| [`de-press-docs/app/ROADMAP.md`](./de-press-docs/app/ROADMAP.md) | Product priorities |
| [`CLAUDE.md`](./CLAUDE.md) | Code rules (some UI-stack parts are outdated — see DESIGN_V2 / PLATFORMS) |

> **This is not medicine and not a replacement for therapy / emergency help.**  
> In a crisis → 112 / 103, not "hold a chatbot".

---

## Where we are now

**Two independent clients + backend** — [`apps/README.md`](./apps/README.md), [ADR 0014](./de-press-docs/app/adr/0014-split-browser-and-mini-app-gpl-shell.md):

| App | Path | Status |
|-----|------|--------|
| **Browser** | `apps/browser/` | standalone web (not a Telegram shell) |
| **Native Android** | `_archive/native/android/` | 🗄 archived (fork Telegram Android, ADR 0016) |
| **Native Desktop** | `_archive/native/desktop/` | 🗄 archived (tdesktop on pause) |
| **Native iOS** | later | after Android |
| **Mini App** | `apps/mini-app/` | parity host inside Telegram (feed, help, helper ops, fund, calls, therapy) |

```
[ product core ✅ ]  [ soft-notify ✅ ]  [ browser UI core ✅ ]  [ circles/voice ✅ ]  [ Mini App ✅ ]  [ multilingual ✅ ]  [ own mobile/desktop ⏳ ]
```

| Layer | Status | Comment |
|------|--------|---------|
| **Domain + ADR** | ✅ | `CONTEXT.md`, ADRs in `de-press-docs/app/adr/` (incl. 0013 four hosts) |
| **Backend** | ✅ | Django + Ninja + Channels: stories, empathy, dialogue+voice, support, notify, helper, AI |
| **Browser (`apps/browser/`)** | ✅ | Standalone Vite SPA; no Mini App / GPL vendor |
| **Mini App (`apps/mini-app/`)** | 🟡 | Standalone app; interim SPA + TG bridge; Web A vendor in `vendor/telegram-tt` |
| **Legacy `_archive/legacy/next-frontend/`** | 🗄 | Next.js — archived |
| **Own Desktop / Own Mobile** | ⏳ | Separate hosts; the Mini App does **not** replace them |
| **Circles** | ✅ | `POST /api/v1/dialogues/{id}/messages/circle` + purge video on close |
| **Voice retention** | ✅ | `GET/POST /me/voice-retention`; per-sender purge on close |
| **Native multilingual (STT/TTS)** | 🗄 | dropped: not feasible without keys; text translation remains ("Translate") |
| **Pilot / prod ops** | ⏳ | staging, secrets, backup, CDN media |

**Bottom line:** the backend MVP is done; circles and voice retention live on the server; the Mini App is at full parity; the tree is frozen as **v1.0.0** (one branch, tagged).  
Next: deploy to the live VPS and the closed pilot cohort.

---

## What the product can do

### Visitor / Hearer

1. Read **Safe Monologues** in the feed (topics, no likes).  
2. **Quiet Phrases** → a private Support Cloud: the guest sends a gesture, no public trace.  
3. **Dialogue Request** — only the author writes, after accept.  
4. **Anti-Panic** ("I'M NOT OK") — kills WS, minimal UI.  
5. **Patterns** — mood notes only in IndexedDB (ZK).  
6. **Help** — crisis guidance + safety + guides.

### Author

- Publish a thought, Hearers (if there is someone to write to), outreach, an inbox of requests, 1-on-1 chat. A cloud is a gesture on your own feed row, not a list under the entry. No pulse in the UI.

### Dialogue

- Text + voice notes; text message translation (the "Translate" button).  
- WS + typing + reconnect + HTTP fallback.  
- Circles: record/preview + `POST …/messages/circle`; files are deleted when the dialogue closes.  
- Soft badges, date chips (Today/Yesterday), same-author bubble stack.

### Helper

- The moderated clouds queue (`/helper`), if `me.is_helper`.

**Invariant:** no public comments, likes, who-heard lists, counters, or reaction lists on an entry page.

---

## Repository structure

```
de-press/
├── CONTEXT.md
├── CLAUDE.md
├── README.md                 ← this file
├── apps/
│   ├── README.md             # Browser ⟂ Mini App (strictly separate)
│   ├── browser/              # ★ browser app (:5174)
│   └── mini-app/             # ★ Telegram Mini App (:5175)
│       ├── src/              # interim SPA + TG WebApp bridge
│       └── vendor/telegram-tt/  # Telegram Web A (GPLv3), fetch script
├── backend/                  # Django + Ninja + Channels (API :8005)
│   ├── apps/                 # Django domain apps (identity, stories, …)
│   ├── api/v1/
│   └── …
├── _archive/                 # 🗄 local archive (legacy Next, native forks) — gitignored, not published
│   ├── legacy/next-frontend/ # old Next.js — not the main UI
│   ├── native/               # fork of Telegram Android / tdesktop (ADR 0015/0016)
│   └── AngelSlim/            # third-party LLM toolkit (clone)
├── de-press-docs/            # product documentation (app + site)
│   └── app/                  # DESIGN_V2, PLATFORMS, ROADMAP, MINI_APP, ADR
└── scripts/
    ├── dev_local.sh
    └── smoke_api.sh
```

**Browser and Mini App share one UI Core** (each app under `apps/`), different hosts. Not two frontend projects.

### Stack

| Layer | Technologies |
|------|------------|
| **UI Core (all hosts)** | Vite 6, React 19, TypeScript, React Router 7, TanStack Query + Virtual, CSS Modules, design tokens |
| **Backend** | Django, Django Ninja, Channels 4, Daphne |
| **DB / cache** | PostgreSQL (required for dev/prod), Redis |
| **AI** | OpenAI-compatible + offline stubs |
| **Styles** | **Strictly no Tailwind** — CSS Modules + CSS variables |

---

## Running the project (locally)

You need: **Python 3.12+**, **Node 20+**, **PostgreSQL 5432**, **Redis** (for Channels).

### 1. Once — Postgres

```bash
sudo -u postgres psql -c "CREATE ROLE depress WITH LOGIN PASSWORD 'depress';"
sudo -u postgres psql -c "CREATE DATABASE depress OWNER depress;"
```

Default variables (put them in a root `.env` or export):

```bash
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=depress
export POSTGRES_USER=depress
export POSTGRES_PASSWORD=depress
export REDIS_URL=redis://127.0.0.1:6379/0
```

> SQLite is **only** for pytest (`DEPRESS_USE_SQLITE=1`). Never run daphne on SQLite.

### 2. Backend (API + WebSocket) — port **8005**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r requirements/local.txt

python manage.py migrate --noinput
python manage.py seed_local        # 3 stories + phrases + demo data
python manage.py check_db          # make sure NAME=depress

# ASGI (Channels / WS)
daphne -b 127.0.0.1 -p 8005 config.asgi:application
```

Check:

```bash
curl -s http://127.0.0.1:8005/api/v1/health
curl -s http://127.0.0.1:8005/api/v1/stories | head -c 200
# OpenAPI: http://127.0.0.1:8005/api/docs
```

### 3. Browser app — port **5174**

```bash
cd apps/browser && npm install && npm run dev
```

Open: **http://127.0.0.1:5174**

### 3b. Mini App (standalone app) — port **5175**

```bash
cd apps/mini-app && npm install && npm run dev
# Telegram Web A sources (GPLv3, large):
./scripts/fetch_telegram_tt.sh
```

Vite proxies `/api`, `/ws` → `:8005`.

### 4. All-in-one script (optional)

```bash
./scripts/dev_local.sh
```

The script: migrate + seed + Daphne `:8005` + Vite app `:5174`.  
Logs: `/tmp/depress_daphne.log`, `/tmp/depress_vite.log`.

### Demo login (seed)

| Field | Value |
|------|--------|
| Email | `seed@de-press.local` |
| Password | `seedseed12` |

In the UI: avatar in the left rail → **Log in**.  
After login: the feed, chat, the email inbox, helper (if you have the role).

### Optional env (AI / soft-notify)

```bash
export AI_API_KEY=...
export AI_BASE_URL=https://api.deepseek.com
export AI_MODEL=deepseek-chat
export PUBLIC_BASE_URL=http://127.0.0.1:5174   # magic-link soft-notify
```

Without an AI key it runs an offline stub (text translation shows an honest offline marker).

### Legacy Next (not needed for normal development)

```bash
cd _archive/legacy/next-frontend && npm install && npm run dev   # :3005, archived
```

---

## UI routes (`apps/browser/`)

| Path | Purpose |
|------|---------|
| `/feed` | The monologue feed (TG-list) |
| `/feed/new` | Publishing a thought |
| `/feed/:id` | Thought card + quiet phrases |
| `/chat` | Dialogues + Dialogue Requests |
| `/chat/:id` | 1-on-1 chat (WS, voice, calls, circles UI) |
| `/patterns` | ZK mood notes (IndexedDB) |
| `/help` | Help / safety / guides |
| `/help/wait` | Waiting for a Helper (the human path) |
| `/help/ai` | AI companion (CompanionPane) |
| `/helper` | The Helper queue (role) |

Shell: **icon rail 72px** · **resizable list** · **main** (see `TG_SHELL_SPEC.md`).

---

## API (briefly)

| | |
|--|--|
| Health | `GET /api/v1/health` |
| Stories | `GET/POST /api/v1/stories`, `GET …/{id}` |
| Empathy | `POST /api/v1/stories/{id}/empathy` |
| Dialogue | requests, accept, messages, voice, **circle**, WS `/ws/dialogues/{id}/` |
| Media prefs | `GET/POST /api/v1/me/voice-retention` |
| Notify | `/api/v1/me/notifications*`, WS `/ws/notifications/` |
| Helper duty | `POST /api/v1/me/helper-duty` `{on}`; `GET /me` `is_on_duty` |
| Help presence | `GET /api/v1/help/presence`; `POST /api/v1/help/heartbeat` |
| Docs | `http://127.0.0.1:8005/api/docs` |

The app client: `apps/browser/src/core/api/client.ts` (mini-app mirror: `apps/mini-app/src/core/api/client.ts`).

---

## Tests

```bash
cd backend && source .venv/bin/activate
DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory pytest -q

# smoke HTTP (needs a live daphne)
./scripts/smoke_api.sh
```

---

## Priorities next

1. **Deploy** — the live VPS by [`DEPLOY.md`](./de-press-docs/app/DEPLOY.md): systemd + nginx, secrets, backups.
2. **Pilot** — a closed cohort; bug reports (`POST /api/v1/bugs`) and the admin console are the feedback loop.
3. **Own desktop** (Tauri over the UI Core) and **own mobile** (PWA-first, ADR 0019).

We do not do: public likes/comments, open matching, a server-side trauma map, AI as a hidden peer; we do **not** count the Mini App as a replacement for our own mobile/desktop.

---

## License

**AGPL-3.0-or-later** — see [`LICENSE`](./LICENSE).  
The vendored Telegram Web A sources in `apps/mini-app/vendor/telegram-tt/` remain **GPLv3** — third-party code, kept as-is and separable.

---

## Principles

1. No public likes / suffering ratings.  
2. No public comments under a story.  
3. The dialogue is initiated by **the author only**.  
4. AI is always labeled; no diagnoses, no toxic positivity.  
5. Emotional maps — device only (ZK).  
6. Anti-Panic outranks the feed and realtime.  
7. Not medicine — a crisis → 112/103.  
8. A Helper is not a therapist by default.  
9. PostgreSQL is required (not SQLite) for the app/API.  
10. No Tailwind — CSS Modules + tokens.  
11. **Form ≈ Telegram ergonomics, color = de-press** (we do not copy GPL tdesktop/Web A code).  
12. **Four hosts:** browser · Telegram Mini App · own desktop · own mobile; one UI Core + one backend ([`PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md)).

---

## Development documentation

- Terms → [`CONTEXT.md`](./CONTEXT.md)  
- **History (how it was built) → [`de-press-docs/HISTORY.md`](./de-press-docs/HISTORY.md)**  
- **Platforms (4 hosts)** → [`de-press-docs/app/PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md)  
- UI design → [`de-press-docs/app/DESIGN_V2.md`](./de-press-docs/app/DESIGN_V2.md)  
- TG geometry → [`de-press-docs/app/TG_SHELL_SPEC.md`](./de-press-docs/app/TG_SHELL_SPEC.md)  
- Roadmap → [`de-press-docs/app/ROADMAP.md`](./de-press-docs/app/ROADMAP.md)  
- Pilot → [`de-press-docs/app/PILOT.md`](./de-press-docs/app/PILOT.md)  
- ADR → [`de-press-docs/app/adr/`](./de-press-docs/app/adr/)
