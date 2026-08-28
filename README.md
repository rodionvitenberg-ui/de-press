# de-press.co

Некоммерческая, эмпатичная платформа-«тихая гавань» для людей, которым тяжело:

**монологи без лайков** · **тихая эмпатия** · **диалог только с согласия автора** · **Anti-Panic** · **ИИ без toxic positivity** · **паттерны только на устройстве**.

| Документ | Зачем |
|----------|--------|
| [`de-press-docs/`](./de-press-docs/) | **Единая документация** (app + site) |
| [`CONTEXT.md`](./CONTEXT.md) | Словарь домена (термины) |
| [`de-press-docs/app/PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md) | **4 hosts**: browser · Mini App · desktop · mobile |
| [`de-press-docs/app/`](./de-press-docs/app/) | Дизайн, роадмап, ADR, пилот |
| [`de-press-docs/app/DESIGN_V2.md`](./de-press-docs/app/DESIGN_V2.md) | ТГ-каркас, темы, аксиомы |
| [`de-press-docs/app/TG_SHELL_SPEC.md`](./de-press-docs/app/TG_SHELL_SPEC.md) | Геометрия shell «как Telegram Desktop» |
| [`de-press-docs/app/ROADMAP.md`](./de-press-docs/app/ROADMAP.md) | Приоритеты продукта |
| [`CLAUDE.md`](./CLAUDE.md) | Правила кода (часть устарела по стеку UI — смотри DESIGN_V2 / PLATFORMS) |

> **Это не медицина и не замена терапии / экстренной помощи.**  
> Кризис → 112 / 103, не «удержи чатботом».

---

## Где мы сейчас

**Два независимых клиента + backend** — [`apps/README.md`](./apps/README.md), [ADR 0014](./de-press-docs/app/adr/0014-split-browser-and-mini-app-gpl-shell.md):

| App | Path | Статус |
|-----|------|--------|
| **Browser** | `apps/browser/` | отдельный веб (не shell Телеги) |
| **Native Android** | `_archive/native/android/` | 🗄 вынесено в архив (fork Telegram Android, ADR 0016) |
| **Native Desktop** | `_archive/native/desktop/` | 🗄 вынесено в архив (tdesktop на паузе) |
| **Native iOS** | later | после Android |
| **Mini App** | `apps/mini-app/` | не product shell |

```
[ product core ✅ ]  [ soft-notify ✅ ]  [ browser UI core ✅ ]  [ circles/voice ✅ ]  [ ★ Mini App ]  [ multilingual ]  [ own mobile/desktop ]
```

| Слой | Статус | Комментарий |
|------|--------|-------------|
| **Домен + ADR** | ✅ | `CONTEXT.md`, ADR в `de-press-docs/app/adr/` (в т.ч. 0013 four hosts) |
| **Backend** | ✅ | Django + Ninja + Channels: stories, empathy, dialogue+voice, support, notify, helper, AI |
| **Browser (`apps/browser/`)** | ✅ | Отдельный Vite SPA; без Mini App / GPL vendor |
| **Mini App (`apps/mini-app/`)** | 🟡 | Отдельный app; interim SPA + TG bridge; vendor Web A в `vendor/telegram-tt` |
| **Legacy `_archive/legacy/next-frontend/`** | 🗄 | Next.js — архив |
| **Own Desktop / Own Mobile** | ⏳ | Отдельные hosts; Mini App их **не** заменяет |
| **Circles** | ✅ | `POST /api/v1/dialogues/{id}/messages/circle` + purge video on close |
| **Voice retention** | ✅ | `GET/POST /me/voice-retention`; per-sender purge on close |
| **Нативный мультиязык** | ⏳ | STT → translate → TTS (не словари UI) |
| **Pilot / prod ops** | ⏳ | staging, secrets, backup, CDN media |

**Итог:** backend-MVP закрыт; кружочки и voice retention на сервере; browser UI Core дожат к v2.0.  
Дальше: Mini App host + нативный мультиязык.

---

## Что умеет продукт

### Visitor / Hearer

1. Читать **Safe Monologue** в ленте (темы, без лайков).  
2. **Тихие фразы** (Quiet Phrase) → private Support Cloud: гость шлёт жест, публичного следа нет.  
3. **Dialogue Request** — диалог пишет только автор после accept.  
4. **Anti-Panic** («МНЕ ХУЕВО») — kill WS, minimal UI.  
5. **Patterns** — mood notes только в IndexedDB (ZK).  
6. **Help** — кризисные ориентиры + safety + гайды.

### Автор

- Публикация мысли, Hearers (если есть кому писать), outreach, inbox запросов, 1-on-1 чат. Облачко — жест на своей строке ленты, не список под записью. Pulse в UI нет.

### Диалог

- Text + voice notes (STT/translate stubs без ключей).  
- WS + typing + reconnect + HTTP fallback.  
- Circles: запись/превью + `POST …/messages/circle`; файлы удаляются при закрытии диалога.  
- Soft badges, date chips (Сегодня/Вчера), same-author bubble stack.

### Helper

- Очередь moderated clouds (`/helper`), если `me.is_helper`.

**Инвариант:** нет публичных комментариев, лайков, who-heard, счётчиков и списков реакций на странице записи.

---

## Структура репозитория

```
de-press/
├── CONTEXT.md
├── CLAUDE.md
├── README.md                 ← этот файл
├── apps/
│   ├── README.md             # Browser ⟂ Mini App (строго раздельно)
│   ├── browser/              # ★ браузерное приложение (:5174)
│   └── mini-app/             # ★ Telegram Mini App (:5175)
│       ├── src/              # interim SPA + TG WebApp bridge
│       └── vendor/telegram-tt/  # Telegram Web A (GPLv3), fetch script
├── backend/                  # Django + Ninja + Channels (API :8005)
│   ├── apps/                 # Django domain apps (identity, stories, …)
│   ├── api/v1/
│   └── …
├── _archive/                 # 🗄 вынесенное из активной зоны (позже в .gitignore)
│   ├── legacy/next-frontend/ # старый Next.js — не основной UI
│   ├── native/               # fork Telegram Android / tdesktop (ADR 0015/0016)
│   └── AngelSlim/            # сторонний LLM-тулкит (клон)
├── de-press-docs/            # документация product (app + site)
│   └── app/                  # DESIGN_V2, PLATFORMS, ROADMAP, MINI_APP, ADR
└── scripts/
    ├── dev_local.sh
    └── smoke_api.sh
```

**Browser и Mini App — один код** (`apps/web/`), разные hosts. Не два frontend-проекта.

### Стек

| Слой | Технологии |
|------|------------|
| **UI Core (все hosts)** | Vite 6, React 19, TypeScript, React Router 7, TanStack Query + Virtual, CSS Modules, design tokens |
| **Backend** | Django, Django Ninja, Channels 4, Daphne |
| **DB / cache** | PostgreSQL (обязателен для dev/prod), Redis |
| **AI / STT** | OpenAI-compatible + offline stubs |
| **Стили** | **Строго без Tailwind** — CSS Modules + CSS variables |

---

## Запуск проекта (локально)

Нужны: **Python 3.12+**, **Node 20+**, **PostgreSQL 5432**, **Redis** (для Channels).

### 1. Один раз — Postgres

```bash
sudo -u postgres psql -c "CREATE ROLE depress WITH LOGIN PASSWORD 'depress';"
sudo -u postgres psql -c "CREATE DATABASE depress OWNER depress;"
```

Переменные по умолчанию (можно положить в корневой `.env` или export):

```bash
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=depress
export POSTGRES_USER=depress
export POSTGRES_PASSWORD=depress
export REDIS_URL=redis://127.0.0.1:6379/0
```

> SQLite **только** для pytest (`DEPRESS_USE_SQLITE=1`). Не запускай daphne на SQLite.

### 2. Backend (API + WebSocket) — порт **8005**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements/local.txt

python manage.py migrate --noinput
python manage.py seed_local        # 3 stories + phrases + demo data
python manage.py check_db          # убедись: NAME=depress

# ASGI (Channels / WS)
daphne -b 127.0.0.1 -p 8005 config.asgi:application
```

Проверка:

```bash
curl -s http://127.0.0.1:8005/api/v1/health
curl -s http://127.0.0.1:8005/api/v1/stories | head -c 200
# OpenAPI: http://127.0.0.1:8005/api/docs
```

### 3. Browser app — порт **5174**

```bash
cd apps/browser && npm install && npm run dev
```

Открыть: **http://127.0.0.1:5174**

### 3b. Mini App (отдельное приложение) — порт **5175**

```bash
cd apps/mini-app && npm install && npm run dev
# Telegram Web A sources (GPLv3, large):
./scripts/fetch_telegram_tt.sh
```

Vite проксирует `/api`, `/ws` → `:8005`.

### 4. Скрипт «всё сразу» (опционально)

```bash
./scripts/dev_local.sh
```

Скрипт: migrate + seed + Daphne `:8005` + Vite app `:5174`.  
Логи: `/tmp/depress_daphne.log`, `/tmp/depress_vite.log`.

### Demo login (seed)

| Поле | Значение |
|------|----------|
| Email | `seed@de-press.local` |
| Password | `seedseed12` |

В UI: аватар в левом rail → **Войти**.  
После логина: лента, чат, уведомления (soft badge), helper (если роль).

### Опциональные env (AI / soft-notify)

```bash
export AI_API_KEY=...
export AI_BASE_URL=https://api.deepseek.com
export AI_MODEL=deepseek-chat
export STT_API_KEY=...
export PUBLIC_BASE_URL=http://127.0.0.1:5174   # magic-link soft-notify
```

Без ключей AI/STT работают offline-stubs.

### Legacy Next (не нужен для обычной разработки)

```bash
cd _archive/legacy/next-frontend && npm install && npm run dev   # :3005, архив
```

---

## UI-маршруты (`apps/web/`)

| Путь | Назначение |
|------|------------|
| `/feed` | Лента монологов (TG-list) |
| `/feed/new` | Публикация мысли |
| `/feed/:id` | Карточка-мысль + quiet phrases |
| `/chat` | Диалоги + Dialogue Requests |
| `/chat/:id` | 1-on-1 чат (WS, voice, circles UI) |
| `/notifications` | Приватные уведомления |
| `/patterns` | ZK mood notes (IndexedDB) |
| `/help` | Помощь / safety / гайды |
| `/helper` | Очередь Helper (роль) |

Shell: **icon rail 72px** · **resizable list** · **main** (см. `TG_SHELL_SPEC.md`).

---

## API (кратко)

| | |
|--|--|
| Health | `GET /api/v1/health` |
| Stories | `GET/POST /api/v1/stories`, `GET …/{id}` |
| Empathy | `POST /api/v1/stories/{id}/empathy` |
| Dialogue | requests, accept, messages, voice, **circle**, WS `/ws/dialogues/{id}/` |
| Media prefs | `GET/POST /api/v1/me/voice-retention` |
| Notify | `/api/v1/me/notifications*`, WS `/ws/notifications/` |
| Docs | `http://127.0.0.1:8005/api/docs` |

Клиент app: `apps/web/src/core/api/client.ts`.

---

## Тесты

```bash
cd backend && source .venv/bin/activate
DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory pytest -q

# smoke HTTP (нужен живой daphne)
./scripts/smoke_api.sh
```

---

## Приоритеты дальше

1. **Нативный мультиязык** (STT → translate → TTS).  
2. **Telegram Mini App host** (этап) — auth, theme bridge, optional bot notify; не единственный mobile.  
3. **Own mobile** (tab-bar + PWA/native) и **own desktop** (shell поверх core).  
4. Pilot ops · production media.

Не делаем: публичные лайки/комменты, open matching, trauma map на сервере, AI как скрытый peer; **не** считаем Mini App заменой своему mobile/desktop.

---

## Принципы

1. Нет публичных лайков / рейтингов страдания.  
2. Нет публичных комментариев под историей.  
3. Диалог инициирует **только автор**.  
4. ИИ всегда помечен; без диагнозов и toxic positivity.  
5. Emotional maps — только device (ZK).  
6. Anti-Panic важнее ленты и realtime.  
7. Не медицина — кризис → 112/103.  
8. Helper ≠ терапевт по умолчанию.  
9. PostgreSQL обязателен (не SQLite) для app/API.  
10. Без Tailwind — CSS Modules + tokens.  
11. **Форма ≈ Telegram ergonomics, цвет = de-press** (не копируем GPL-код tdesktop/Web A).  
12. **Четыре hosts:** browser · Telegram Mini App · own desktop · own mobile; один UI Core + один backend ([`PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md)).

---

## Документация для разработки

- Термины → [`CONTEXT.md`](./CONTEXT.md)  
- **Платформы (4 hosts)** → [`de-press-docs/app/PLATFORMS.md`](./de-press-docs/app/PLATFORMS.md)  
- Дизайн UI → [`de-press-docs/app/DESIGN_V2.md`](./de-press-docs/app/DESIGN_V2.md)  
- TG geometry → [`de-press-docs/app/TG_SHELL_SPEC.md`](./de-press-docs/app/TG_SHELL_SPEC.md)  
- Roadmap → [`de-press-docs/app/ROADMAP.md`](./de-press-docs/app/ROADMAP.md)  
- Пилот → [`de-press-docs/app/PILOT.md`](./de-press-docs/app/PILOT.md)  
- ADR → [`de-press-docs/app/adr/`](./de-press-docs/app/adr/)
