# AUDIT v1.0.0 — полный аудит проекта de-press

Дата: 2026-09-01. База: git `main` @ v1.0.0, чистое дерево.
Охват: архитектура (11 backend-приложений, 3 клиента, 22 ADR), код-ревью сервисного слоя, безопасность (authz, лимиты, токены, приватность), матрица endpoint↔клиент, документация.

## ✅ Базлайны

| Проверка | Результат |
|---|---|
| browser: vitest + build | 69/69 ✅, build ✅ |
| mini-app: vitest 13/13 + build; admin: build | ✅ / ✅ |
| backend: pytest по 10 чанкам (`timeout 240`, sqlite, CHANNEL_LAYER=memory) | **10/10 exit=0** |
| Полный `pytest` одним прогоном | ✅ exit=0, ~6.5–7 мин, 1 skip — Q1 закрыт: «висение» было артефактом окружения |

## Подтверждённые инварианты (чисто)

- **Actor-seam** (`api/deps.py`, `identity/services.py`) — единая точка резолва субъекта, сервисы не видят raw request.
- **WS-консьюмеры** (dialogue, notifications) — проверка участия, flood control, группы строго по actor.
- **Эмпатия** — pulse/hearers только автору (403 для остальных).
- **AI crisis short-circuit** в `ai/crisis.py`.
- **Блокировки** (`moderation/blocks.py`) — `is_blocked_between` корректно обрабатывает все 4 комбинации account/session в обе стороны.
- **ZK-инвариант клиента** — mood-паттерны только в IndexedDB (`core/memory/db.ts`), есть `wipeAllMemory`, отправок на сервер нет.
- **`kids/`** — sim-харнесс изолирован: только management-команда `sim_kids`, в API не экспонирован.
- **PRIVACY.md подтверждён кодом**: солёный SHA-256 IP только в Redis TTL (`api/v1/i18n.py:40-42`), голосовые/кружки удаляются при закрытии диалога (`dialogue/services.py:1029-1057`), логирования с PII нет.
- **ADR актуальны**: supersessions оформлены в тексте (0008→0017).

---

## 🔴 Корректность / безопасность

### B1. Magic-токен почтового инбокса бессрочный — СТАТУС: ✅ исправлено (2026-09-01)
`notifications/softnotify.py:160-193` + `notifications/models.py:119`: `EmailDigest.token` не имеет срока жизни. `open_inbox` для аккаунта делает `django_login` — ссылка из письма = вечный credential входа в аккаунт.
**Исправление:** константа `MAGIC_LINK_TTL_DAYS = 14`; `resolve_digest` проверяет возраст `created_at` и отдаёт «Ссылка устарела» (endpoint `/auth/inbox` → 400). Тест `test_open_inbox_expired_token`. Без миграции (проверка по существующему `created_at`). Верификация: `apps/notifications` — 19/19 зелёные.

### B2. Блокировка скрывает ленту только в одну сторону — докстринг противоречит коду
`moderation/blocks.py:175-197`: докстринг `blocked_author_q_for_viewer` обещает «(or who blocked viewer — hide mutual)», но Q строится только по `blocker=viewer`. Итог: если B заблокировал A, A продолжает видеть истории B в ленте.
**Решение (2026-09-01):** оставлено одностороннее скрытие как намеренное; докстринг приведён в соответствие («one-way: authors who blocked the viewer stay visible»). Код не менялся.

### B3. Орфан-кластер: модерация запросов на диалог без UI — СТАТУС: ✅ исправлено (2026-09-01)
`api/v1/moderation.py:194-215` — `GET /moderation/dialogue-requests` + `/approve` + `/reject`. Ни один клиент их не вызывает (browser — только `/moderation/clouds*`, admin — только `/admin/*`). Поток `DialogueRequest` (`dialogue/models.py:19-22`): `PENDING → (модерация?) → AWAITING_HELPER → accept` — модерация недостижима из UI.
**Решение:** экран модерации. В панель Helper (`apps/browser/src/features/helper/HelperQueue.tsx`) добавлен таб «Запросы диалога» (`AWAITING_HELPER`-инбокс, approve → PENDING к автору, reject → DECLINED), 3 метода в api-клиенте. Реиспользованы осиротевшие i18n-ключи `review*`; добавлен один `tabRequests` (en/ru/types). Бэкенд не менялся. Верификация: browser vitest 69/69, `tsc -b && vite build` — ок.
**Примечание:** `list_review_inbox` — legacy-гейт («New requests skip this gate»), отдаёт только `AWAITING_HELPER` и требует `is_helper && is_on_duty`, поэтому в обычном режиме таб пуст — это ожидаемо (пустые состояния покрыты).

## 🟡 Качество

### Q1. Полный pytest висит на teardown — ✅ закрыт как «не воспроизводится» (2026-09-01)
Чистый одиночный прогон проходит полностью: `[100%]` → **exit 0** за ~6.5–7 мин (на нагруженной машине, load 6.7), RSS ≤ 167 МБ, 1 skip (`config/tests/test_channel_layer.py` — «CHANNEL_LAYER is not redis», ожидаемо при memory-слое). Профилирование опровергло гипотезу «не-демон поток / не закрытый event loop»: память стабильна по всему прогону (162→166 МБ), процесс завершается сам, `PYTEST_EXIT=0`. Строка-итог отсутствовала в логах только из-за `-q` из pytest.ini + `-q` в CLI = `-qq` (pytest скрывает summary). Наблюдения при аудите — артефакты: параллельные экземпляры pytest на одном sqlite, kill дочернего процесса обёрткой при штатном выходе команды запуска, memory-pressure машины (swap 3.9/4 GiB). **Каноническая команда полного прогона** (один экземпляр!): `cd backend && timeout 1200 env -u DEEPSEEK_API_KEY DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory .venv/bin/python -m pytest -o addopts= -q` — с `-o addopts=` чтобы видеть summary. Для CI: одиночный прогон заблокирован только временем (~7 мин), не зависанием.

### Q2. Гонка в i18n rate-limit — ✅ исправлено (2026-09-01)
`api/v1/i18n.py:49-58`: `cache.get` → `cache.set(1)` / `cache.incr` — check-then-act (два параллельных первых запроса оба видят `None` → счётчик недосчитывается). Общий `common/rate_limit.py` чист (счёт по строкам БД). **Фикс:** атомарный `cache.add(key, 1, RATE_WINDOW)` (set-if-absent) + прежняя ветка `incr`/fallback; семантика сохранена (20 загрузок проходят, 21-я → 429). Регрессионный тест `test_ui_catalog_rate_limit_caps_language_loads` (уникальные payload'ы — кеш каталога проверяется до rate-limit; уникальный аккаунт → изолированный ключ). Verified: `apps/common/tests/test_i18n_api.py + test_i18n_ui.py` — 8 passed.

### Q3. Дублирование browser↔mini-app клиентов — ✅ исправлено (2026-09-01)
**Фикс:** общий `packages/api-client` (`@de-press/api-client`; в обоих приложениях зависимость `file:../../packages/api-client`, workspaces не вводились): рукописная логика (`request`, `ApiError`, SSE-стрим `aiSupportStreamRequest`, `postStoryVoice`) и типы — один источник; файлы приложений стали шимами-реэкспортами (72 точки импорта не тронуты). Эндпоинты объединены в супермножество (95 путей): mini получил пины/муты/forward/edit/delete/reopen диалогов и `publishStoryVoice`, browser — `loginTelegram` и `testTelegramDigest` (рассинхрон устранён). Конфликты типов решены в пользу более широкого варианта (`Dialogue.story_id: string | null`, `NotificationKind` — 12 видов, `SupportCloud.image_url`/`phrase_key`, `ChatMessage.reply_to` и др.). Кодогенерация: `npm run gen:api` в пакете (`openapi-typescript` по `/api/openapi.json`; схема проверена — 105 путей, 85 именованных схем) → `src/schema.gen.d.ts` закоммичен; перевод рукописных типов на сгенерированные — отдельный шаг (ADR 0023). Verified: `npm run build` (tsc -b + vite) — browser и mini ок; `npm test` — browser 69 passed, mini 13 passed.

### Q4. mini-app: нет тестов и нет code-splitting — ✅ исправлено (2026-09-01)
**Фикс:** vitest добавлен по образцу `apps/browser` (devDep `^4.1.11`, скрипт `npm test`, `test.environment: "node"` в `vite.config.ts`, vendor/telegram-tt исключён из прогона). Дым-тесты (13, colocated): `core/api/client.test.ts` (JSON-парсинг, `ApiError`+status, не-JSON 500 → statusText, 204, `Content-Type`), `core/host/startParam.test.ts` (каталог, UUID-нормализация, helper_join, anti-panic, неизвестные), `core/host/telegram.test.ts` (детект TG-host). Code-splitting: `React.lazy`+`Suspense` для patterns/therapy/help(+wait/ai)/helper — главный чанк **537 → 482 kB**, тяжёлое — в 7 on-demand чанков (TherapyPane 32 kB, включивший `qrcode`). Verified: `npm test` — 13 passed; `npm run build` (tsc + vite) — ок.

### Q5. AI offline-gateway определяет стабы по имени класса — ✅ исправлено (2026-09-01)
`apps/ai/services.py:108,140` — `gateway.__class__.__name__ == "OfflineGateway"`. **Фикс:** явный флаг в протоколе `AIGateway` (`is_offline: bool`), `OfflineGateway.is_offline = True`, `OpenAICompatibleGateway.is_offline = False`; в services — `gateway.is_offline`. Фейк в тестах (`ExplodingGateway`) дополнен `is_offline = False` (протокол теперь требует атрибут). Verified: `apps/ai` — 13 passed.

### Q6. Cookie анонимной сессии — «голый» UUID — ✅ исправлено (2026-09-01, принято решение реализовать)
**Фикс:** значение cookie подписывается `django.core.signing` (HMAC от `SECRET_KEY` + salt `depress.anon-session`): новый `apps/identity/cookies.py` (`sign_anon_session_id` / `resolve_anon_session_id`, окно подписи = `ANON_SESSION_COOKIE_MAX_AGE` = 1 год). Единый источник на **обе** точки чтения: HTTP (`identity/middleware.py`) и WS (`dialogue/middleware.py`, включая fallback `?anon=` — он теперь тоже требует подписанное значение; вне фронта/тестов не использовался). Голый/поддельный UUID отбрасывается до похода в БД. Тесты: новый `apps/identity/tests/test_cookies.py` (подписанное резолвится, голый UUID/подделка/пустое — нет, middleware игнорирует legacy-cookie), обновлены `therapy` (anon_client), `dialogue` (test_calls WS-handshake), `notifications` (assert через резолвер). **Миграция:** при выкатке все существующие анонимные cookie инвалидируются разово — посетители получают новую анонимную сессию (осознанное продуктовое решение).

### Q7. Нулевая наблюдаемость сервера — ✅ исправлено (2026-09-01)
**Фикс:** минимальный `LOGGING` в `config/settings/base.py`: root → console `WARNING`, `django.request` → `ERROR` (видны только 500-е, без тел запросов и payload'ов), `apps` → `ERROR`, `django.server` → `INFO` с собственным handler'ом (строки runserver в dev сохранены; настройка заменяет DEFAULT_LOGGING). Verified: settings-импорт + `config apps/notifications` — 20 passed, 1 skipped. Audit-trail модерации сознательно не добавлялся (отдельная фича, вне рамок аудита).

## 🟢 Документация

### D1. CLAUDE.md описывает несуществующий фронтенд — ✅ исправлено (2026-09-01)
Стек-секция мандировала Next.js/App Router (фактически — Vite SPA ×3, Next.js только в архиве); «Django REST Framework» → Django Ninja (DRF в requirements нет); несуществующий `apps/web/…` → `src/styles/tokens.css` browser/mini-app (admin — `admin.css`); R3F/GSAP и `use3DScroll` убраны (в текущих package.json их нет); команды переписаны под per-app npm-скрипты (lint-скрипта нет ни у одного приложения); закрыт незакрытый code-fence в конце файла.

### D2. Два CONTEXT.md — 149-строчные близнецы с 3 расхождениями — ✅ исправлено (2026-09-01)
Git-история инвертировала исходное направление: `de-press-docs/CONTEXT.md` замер на коммите 9374a8a, а корневой обновлён EN-переводом (2834033, «Q6, RU archived in docs-ru-archive/»). **Решение:** канон — корневой `CONTEXT.md`; `de-press-docs/CONTEXT.md` заменён указателем (ссылки из `de-press-docs/README.md` остаются живыми).

### D3. Терминология кода против глоссария — ✅ исправлено (2026-09-01, выбран вариант «сноска»)
Глоссарий (корневой `CONTEXT.md`, канонический): Story — «без публичных комментариев», avoid: *post*. В коде: роут `/stories/{id}/comments` + `comments/voice`, сервис `add_comment`, ключ `post_id` (`support/services.py:92`). **Решение:** добавлена сноска-«Naming note» к термину Story в `CONTEXT.md` (роуты реализуют авторское продолжение монолога, а не публичную ленту комментариев; имена сохранены ради стабильности API). Переименование — ломающее API-изменение, отложено до версионирования API.

## Матрица endpoint↔клиент

- backend 105 уникальных путей; browser покрывает 90, mini — 86, admin — 4+.
- Ложные сироты исключены (пути через `${API_URL}` и query-strings учтены вручную).
- Реальные необслуживаемые: кластер B3; `/me/notifications*` REST у браузера не вызывается намеренно (WS покрывает); `/fund/report`, `/help/dashboard`, `/stories/voice` — односторонние фичи клиентов, по дизайну.

## Ограничения аудита

- `dialogue/services.py` (1532 строки) читался выборочно (карта + ключевые функции).
- Dead-code pass по бэкенду точечный (kids, логирование, орфаны).
- JS-бандлы (dist) не анализировались, кроме как источник ложных срабатываний матрицы.

## Рекомендуемый порядок

1. **B1** (токен) — маленький и самый безопасный для приватности.
2. **B2** — решить продукт-вопрос «mutual hide?» → 10 строк.
3. **B3 / D1 / D2** — решения, потом механическая работа.
4. **Q1** — разблокировать цельный CI-прогон.
5. Остальное — по мере касания.

