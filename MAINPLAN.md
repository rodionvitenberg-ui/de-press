# MAINPLAN — два агента, две ветки, один backend

После утверждения этого документа создать в корне репозитория:

- `MAINPLAN.md` — этот текст (контракт на работу)
- `PROGRESS.md` — живой журнал; оба агента дописывают его в **конце каждой задачи**

Не начинать фичи, пока Gate 0 не закрыт.

---

## Кто что ведёт

| | Агент A — **Grok** (эта сессия) | Агент B — **второй агент** |
|---|---|---|
| Ветка git | `feat/agent-a-helper-ops` | `feat/agent-b-companion-hosts` |
| Тема | Роль Helperа в browser + backend | ИИ-компаньон, Mini App, мультиязык, hosts |
| База | `main` после Gate 0 | `main` после Gate 0 |

Grok только что собирал Help Request — контекст Helperа горячий, поэтому Track A здесь. Второй агент не дублирует browser-Help и не трогает `dialogue.help`.

---

## Стек (не отходить)

Общий backend: Django + Ninja + Channels, Postgres обязателен (SQLite только pytest), Redis для WS.

Browser и Mini App — **два приложения**, ADR 0014. Не импортировать `apps/mini-app/vendor` в browser. Без Tailwind: CSS Modules + токены `--bg-main`, `--bg-surface`, `--text-primary`, `--text-muted`, `--accent-hope`.

ИИ: существующий OpenAI-compatible gateway (DeepSeek / офлайн-стаб). Не менять провайдера «заодно». Промпты: валидация чувств, без диагнозов, без toxic positivity. ИИ всегда помечен. Anti-Panic **не** зовёт ИИ.

Домен: Helper ≠ терапевт ≠ 112. Кризис → 112/103. Нет публичных лайков/комментов. Паттерны и память компаньона — только устройство (ZK).

---

## Gate 0 (только Grok, до параллели)

Репозиторий только что получил git. Фича HELP лежит на `feat/help-human-ai` (14 коммитов после `99723a4`). Remote нет.

1. Руками пройти `/help` на http://127.0.0.1:5174 (карточки, wait, accept Helperом, `/help/ai`, телефонный viewport).
2. Слить `feat/help-human-ai` → `main` локально.
3. Создать от `main`: `feat/agent-a-helper-ops` и `feat/agent-b-companion-hosts`.
4. Положить в корень `MAINPLAN.md` и `PROGRESS.md`, закоммитить в `main`.
5. Написать в `PROGRESS.md` строку Gate 0 = done.

Пока Gate 0 не done, агент B **не** стартует (иначе разъедутся базы).

---

## Track A — Grok: Helper ops

Порядок внутри трека **жёсткий**. Каждый пункт — отдельный коммит-пакет, зелёные тесты, запись в `PROGRESS.md`.

### A1. Репорт в help-чате без Story

Сейчас `Report.story` обязателен; `submit_message_report` падает, если `dialogue.story_id is None`.

- `Report.story` → `null=True`; XOR: есть story или есть message (help-чат).
- Уникальность open-репорта для help: по `(message, from_account|from_session)`, не по story.
- UI: репорт в `DialoguePage` работает при `source=help`.
- Файлы: `backend/apps/moderation/**`, `backend/api/v1/moderation.py`, при необходимости `MessageMenu.tsx`.

### A2. Проверка Dialogue Request Helperом

Плашка «мы проверили — вам безопасно» уже в UI и **лжёт**. Helper должен видеть запрос до автора.

- Статус: `awaiting_helper` → после approve автором виден как `pending` (принять/отклонить как сейчас). Reject Helperом → `declined`, автор не видит серую строку.
- Inbox автора `GET /api/v1/me/dialogue-requests` — только уже проверенные.
- Inbox Helperа: `GET /api/v1/moderation/dialogue-requests` + approve/reject.
- UI Helperа: серые строки в `/chat` **ниже** Help Request, **выше** авторских Dialogue Request. `/helper` не делать вторым инбоксом разговоров.
- Notify: Helperам `dialogue_request_review`; автору существующий `dialogue_request` только после approve.
- Файлы: `backend/apps/dialogue/models.py` (статус), `services.py` (`create_request` / `list_inbox` / новые approve), `api/v1/dialogue.py` или `moderation.py`, `ChatList.tsx` (Grok уже владеет этим файлом).

### A3. Онбординг Helperа

Сейчас только `is_helper` в Django admin.

- Staff/существующий Helper создаёт **одноразовый инвайт** (токен, org, TTL).
- Кандидат (аккаунт) открывает `/helper/join?token=` → короткий pledge (не врач, не 112, можно уйти) → `is_helper=True`, `helper_org` с инвайта.
- Нет открытой самозаписи «стать Helperом».
- Список инвайтов — в дашборде (A4), не публично.
- Файлы: `backend/apps/identity/**` (модель инвайта), новый `api/v1/helper_invite.py`, `apps/browser/src/features/helper/HelperJoin.tsx`, пункт в UserMenu только у staff.

### A4. Дашборд модерации

API `GET /api/v1/moderation/dashboard` жив, UI нет.

- `/helper` становится две вкладки: **Облачка** (текущая очередь) + **Сводка** (числа дашборда + последние репорты, без публичных счётчиков страдания).
- Репорты help-чатов из A1 видны в сводке.
- Не тащить сюда Help Request и Dialogue Request (они в `/chat`).
- Файлы: `HelperQueue.tsx` + css, client уже имеет dashboard.

### A5. Дежурство

- Поле `is_on_duty` (или эквивалент) на Account-Helper. Тумблер в `/helper` сводке и/или UserMenu.
- `POST /api/v1/me/helper-duty` `{on: bool}`.
- Notify и inbox Help Request / dialogue-review — **только** `is_helper && is_on_duty && is_active`. Если никто не на смене — wait как сейчас + 112 + ссылка на ИИ. Не обещать «ответ за 30 секунд».
- Файлы: identity model, `dialogue/help.py` (`_notify_helpers`, `list_help_inbox`), ChatList не обязателен.

### A6. Онлайн + мгновенный матч

Только после A5.

- Heartbeat: Helper с открытым `/chat` или `/helper` шлёт ping (HTTP каждые 20с или лёгкий WS). «Онлайн» = ping < 45с.
- Если есть дежурный **и** онлайн — Help Request назначается одному (round-robin / least-recent), сразу `Dialogue source=help`, wait сразу «открыть чат». Остальные не видят строку.
- Если никого — очередь A5.
- Публично не светить имена и «N хелперов онлайн». Максимум для ждущего: «сейчас кто-то на смене» / «сейчас никого у экрана».
- Файлы: `dialogue/help.py`, тонкий `presence` (новый модуль, не раздувать `help.py` бесконечно), `HelpWaitPane.tsx`.

---

## Track B — второй агент: компаньон и hosts

Не ждать A2–A6, кроме контрактов ниже. Стартовать после Gate 0.

### B1. Стриминг ИИ + память IndexedDB

- Новый endpoint **рядом**, не ломая POST `/api/v1/ai/support`: например `POST /api/v1/ai/support/stream` (SSE). Старый POST остаётся для тестов и Mini App до порта.
- Gateway: `stream` у OpenAI-compatible client. Офлайн-стаб — одним куском (или по предложениям).
- Кризисный short-circuit — без «красивой печати» инструкций 112.
- IndexedDB: новый store в `apps/browser/src/core/memory/` (версия DB +1), **не** класть реплики в `mood_entries`. На сервер по-прежнему последние ≤12 реплик за ход.
- Стереть память — тем же wipe, что паттерны, отдельным подтверждением «и диалоги с ИИ».
- UI: только `CompanionPane.tsx` (+ css). Не строка в `/chat`. Anti-Panic не звать.
- Файлы: `backend/apps/ai/**`, `backend/api/v1/ai.py`, `CompanionPane.*`, `core/memory/db.ts`.

### B2. Mini App parity

`apps/mini-app` — отдельное дерево. Сейчас Help статичный, нет `/help/wait`, `/help/ai`, нет серых Help Request в чатах. Telegram auth уже есть.

- Перенести (копировать, не общий пакет) HELP-карточки, wait, companion, help-inbox в ChatList, join Helperа если A3 уже в `main`.
- `startapp`: `help_wait`, `help_ai`, `helper_join`.
- Не начинать интеграцию `vendor/telegram-tt` в этом пункте.
- Если API A5/A6 ещё нет — duty/match просто отсутствуют в Mini App (очередь как сейчас).
- Файлы: **только** `apps/mini-app/**`. Запрещено импортировать из `apps/browser`.

### B3. Нативный динамический мультиязык

Контент, не словари UI. Уже есть STT/translate стабы в `backend/apps/dialogue/speech.py`.

- Цепочка STT → translate → TTS для голосовых в Initiated Dialogue (включая help-чаты).
- Язык цели — locale актора (уже есть UI locale). Маркер офлайна, если нет ключа.
- Не подменять i18n-каталог интерфейса этим пайплайном.
- Файлы: `speech.py`, API transcribe/translate (уже частично), `VoiceBubble` / composer в **mini-app** если B2; **browser** VoiceBubble — только если Grok не держит файл. Правило: browser `features/chat/VoiceBubble.tsx` и `DialoguePage.tsx` принадлежат **Grok** для A-трека. B3 в browser — отдельный согласованный слот в `PROGRESS.md` («B3-browser-voice: waiting for A idle»), либо B3 сначала только API + Mini App, browser-voice — после A6.

### B4. Own mobile / own desktop (горизонт внутри трека, не store-релиз)

Не «опубликовать в сторах». Первый конкретный выход:

- Зафиксировать ADR-дополнение: Mini App ≠ own mobile.
- Browser PWA уже live — описать, чего не хватает до own mobile (push, store chrome).
- Own desktop: выбор оболочки (Tauri vs отложенно) одним ADR, без большого нативного кода в этом MAINPLAN.
- Папка `native/` если появится — только агент B.

---

## Владение файлами (конфликт = нарушение плана)

### Только агент A (Grok)

```
backend/apps/dialogue/help.py
backend/apps/dialogue/models.py          # HelpRequest, DialogueRequest statuses, Dialogue.story
backend/apps/dialogue/services.py        # request/accept/outreach; не speech.py
backend/apps/identity/**
backend/apps/moderation/**
backend/api/v1/help.py
backend/api/v1/moderation.py
backend/api/v1/identity.py
apps/browser/src/features/help/HelpPane.*
apps/browser/src/features/help/HelpWaitPane.*
apps/browser/src/features/helper/**
apps/browser/src/features/chat/**         # ChatList, DialoguePage, menus, voice в browser
apps/browser/src/components/layout/UserMenu.tsx
```

### Только агент B

```
backend/apps/ai/**
backend/api/v1/ai.py
backend/apps/dialogue/speech.py
apps/browser/src/features/help/CompanionPane.*
apps/browser/src/core/memory/**
apps/mini-app/**                          # всё дерево
```

### Общие файлы — протокол, не свободная правка

| Файл | Как трогать |
|------|-------------|
| `apps/browser/src/App.tsx` | Добавлять **только свой** `<Route>`. Не переставлять чужие. |
| `apps/browser/src/core/api/client.ts` + `types.ts` | Добавлять методы/типы в конец своего блока. Не реформатировать файл. |
| `apps/browser/src/core/i18n/messages/ru.ts` `en.ts` `types.ts` | A: `help.*` кроме companion, `helper.*`, `me.*`, `shell.safetyBanner`. B: `companion.*`. Новые ключи только append. Не переименовывать чужие. |
| `apps/browser/src/core/hooks/useNotifications.ts` | A добавляет kinds review/duty. B не добавляет kinds без строки в PROGRESS. |
| `backend/api/main.py` | Одна строка `add_router` за раз, алфавит/конец списка. |
| `backend/apps/notifications/models.py` | Новые `NotificationKind` — сначала строка в PROGRESS «claim: kind=…», потом коммит. |
| `CAPABILITIES.md` `README.md` `CONTEXT.md` | Дописывать строки/абзацы своей фичи. Не переписывать таблицы целиком. |
| `MAINPLAN.md` | Менять только по согласованию обоих (или человека). |
| `PROGRESS.md` | Оба пишут; не удалять чужие строки. |

Если нужен файл из чужой зоны — **стоп**, строка `blocked-on: A|B` в PROGRESS, не «маленький патч в чужом файле».

---

## Контракты API (B может опираться, когда A напишет `contract:ready` в PROGRESS)

Уже в `main` после Gate 0:

```
POST /api/v1/help/requests
GET  /api/v1/help/requests
GET  /api/v1/help/requests/mine
POST /api/v1/help/requests/{id}/accept|skip|cancel
POST /api/v1/ai/support
GET  /api/v1/moderation/dashboard
POST /api/v1/auth/telegram
```

A2 добавит (имена зафиксировать в PROGRESS при коммите):

```
GET  /api/v1/moderation/dialogue-requests
POST /api/v1/moderation/dialogue-requests/{id}/approve
POST /api/v1/moderation/dialogue-requests/{id}/reject
```

A3:

```
POST /api/v1/helper-invites
POST /api/v1/helper-invites/{token}/accept
```

A5–A6:

```
GET  /api/v1/me
     + is_on_duty, maybe presence
POST /api/v1/me/helper-duty
GET  /api/v1/help/presence     # { someone_on_duty: bool, someone_online: bool } без счётчиков людей
```

B1:

```
POST /api/v1/ai/support/stream   # SSE; старый /support не удалять
```

---

## Журнал `PROGRESS.md` (формат)

Каждая запись — блок, не эссе:

```markdown
## YYYY-MM-DD HH:MM  agent=A|B  id=A2
status: started | blocked-on:A3 | contract:ready | done
branch: feat/agent-a-helper-ops
commit: abc1234
notes: one line
files: list of paths touched
api: METHOD /path  (if contract)
```

Правила:

- Перед началом задачи — `status: started`, чтобы второй не взял то же.
- После API, которым пользуется другой — `contract:ready` + точный path.
- `blocked-on` обязателен, если ждёшь чужой файл/контракт.
- Не ребазить чужую ветку. На `main` — только после Gate 0 и явных merge от человека.

---

## Что не делаем в этом MAINPLAN

- Токсичная позитивность, диагнозы, ИИ как скрытый пир в `/chat`.
- Публичные лайки, комменты, витрина «N хелперов онлайн».
- Duty hours календаря (cron смены) — только тумблер «на смене».
- Публиковать Mini App на Web A shell и сторы native.
- Общий npm-пакет между browser и mini-app.

---

## Критерий «трек закрыт»

**A:** help-чат репортится; Dialogue Request сначала у Helperа; инвайт-онбординг; дашборд на `/helper`; дежурство режет нотификации; при онлайн-дежурном Help Request открывает чат сразу.

**B:** `/help/ai` стримит и помнит на устройстве; Mini App умеет те же HELP-пути и telegram login; голосовые переводятся по пайплайну STT→translate→TTS хотя бы в Mini App + API; ADR по own desktop/mobile записан, кода стора нет.

Человек мержит ветки в `main`. Агенты не форсят push.
