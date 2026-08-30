# Roadmap de-press.co

См. также [README.md](../README.md) (стадия и приоритеты), [CONTEXT.md](../CONTEXT.md), [PILOT.md](./PILOT.md).

## Стадия (2026-08)

**Product core v0.0–v0.14 закрыт в коде.**  
**P1 «Soft-notify» закрыт** (включая `/inbox` по magic-token и `PUBLIC_BASE_URL` в settings).  
**Browser host (UI Core v2)** — Vite SPA с ТГ-эргономикой: каркас + дожим P0 закрыт.  
**Кружочки + voice retention на сервере закрыты.**  
Дальше по продукту: **нативный динамический мультиязык** (P1).  
По hosts: **Telegram Mini App** (этап), затем/параллельно **own mobile** и **own desktop**.  
**AI-помощник (полный продукт) — в самую последнюю очередь.**  
В browser уже есть Help human/AI paths (`/help`, `/help/wait`, `/help/ai` CompanionPane) — это companion surface, не закрытый AI-помощник.

**Терапия (ADR 0022, stage B) закрыта в браузере и Mini App** (Solana Pay QR + ручное подтверждение терапевта). Вопросы новой фазы — [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md), план — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md).

> **Решение (2026-08, уточнено):** этот репозиторий — только приложения.  
> **Четыре App Hosts:** browser · Telegram Mini App · own desktop · own mobile — см. [`PLATFORMS.md`](./PLATFORMS.md), [ADR 0013](./adr/0013-four-app-hosts.md).  
> Mini App — одна платформа и интересный этап, **не** замена своим mobile/desktop.  
> Лендинг — отдельный репозиторий; связь — ссылка-переход.

```
[ product core ✅ ]  [ soft-notify ✅ ]  [ browser UI core ✅ ]  [ circles/voice ✅ ]  [ ★ Mini App этап ]  [ multilingual ]  [ own mobile/desktop ]
```

## Уже сделано

| Версия | Содержание | Статус |
|--------|------------|--------|
| v0.0–v0.7 | Foundation, safety, monologue, dialogue, Anti-Panic, AI, ZK patterns, help static | ✅ |
| WS | Channels, typing, reconnect | ✅ |
| Pilot docs | PILOT.md, smoke | ✅ |
| **v0.9** | Quiet Phrases + private Support Clouds (templates) | ✅ |
| **v0.10** | Hearer List + Author Outreach | ✅ |
| **v0.11** | Moderated free-text + Helper + queue | ✅ |
| **v0.12** | Design pass (clouds, author vs public) | ✅ |
| **v0.13** | i18n ru/en + phrase texts | ✅ |
| **v0.14** | Voice notes + translate | ✅ |
| **P1 notify (full)** | Notification + EmailDigest + WS + REST + настройки + `/inbox` + `PUBLIC_BASE_URL` | ✅ |

## P1 «Soft-notify» — закрыт ✅

- ✅ `Notification` (kind, payload, is_read) + `EmailDigest` (magic-token, статусы) + миграции
- ✅ REST: `/me/notifications`, `unread-count`, `mark-read`, `read-all`
- ✅ WS `/ws/notifications/` (snapshot, new, read, unread_count, ping) + Anti-Panic kill
- ✅ `notify()` из dialogue и support (запросы диалога, облачка, approve, сообщения, outreach)
- ✅ `/me/notify-settings` (opt-in, частота, contact email) + тест дайджеста
- ✅ **`POST /auth/inbox`** — вход по magic-token (account → login, anon → bind anon-cookie)
- ✅ **Страница `/inbox`** (`?token=...`) — открывает приватный инбокс, отмечает прочитанные
- ✅ **`PUBLIC_BASE_URL`** вынесен в settings/env (softnotify использует `settings.PUBLIC_BASE_URL`)
- ✅ Тесты: open_inbox (account/anon/invalid) + tsc чист

## Дальше (новый порядок приоритетов)

| Приоритет | Содержание |
|-----------|------------|
| **P0 ✅** | **UI Core / Browser host**: Vite + React SPA, токены/темы, 3-зонный ТГ-каркас, лента/чат, «МНЕ ХУЕВО» |
| **P0 ✅** | **Кружочки**: `POST …/messages/circle` + ephemeral purge on close |
| **P0 ✅** | **Голосовые с опцией удаления**: `/me/voice-retention` + per-sender purge on close |
| **P0** | **Хвосты паритета browser ↔ Mini App**: фонд (FundCard/TipBanner/TipWalletForm), решение по calls — [OPEN_QUESTIONS.md](./OPEN_QUESTIONS.md) Q2; терапия в Mini App ✅ |
| **P0** | **Хелперский дашборд**: вкладка слева, видна только хелперам; очередь, приём → диалог, сводка — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md) |
| **P0** | **Подготовка репозитория + перевод документации на EN + полный ретест → ручная QA** — [PARITY_QA_PLAN.md](./PARITY_QA_PLAN.md) |
| 🗄 снято | **Нативный динамический мультиязык** (STT → translate → TTS) — снято: без ключей адекватно не реализовать; остался перевод текста |
| **P1** | **Telegram Mini App host (этап)**: Bot + Mini App, initData auth, theme bridge, optional bot soft-notify; диалоги остаются на de-press backend — **не** замена own mobile |
| **P1** | **Own Mobile**: ТГ-таб-бар layout → PWA / нативная обёртка / store (отдельный host) |
| **P1** | **Own Desktop**: обёртка UI Core (Tauri / Electron — решение позже) |
| **P1 ✅** | **PWA bridge on browser host** — installable standalone + phone/tablet chrome; native store still later. Prod-build verified (manifest+icons 200, sw.js served, install row in More, offline shell per sw.js); live phone install — pilot QA. See [`MOBILE_PWA.md`](./MOBILE_PWA.md) |
| 🗄 → лендинг | **Публичные страницы (помощь, гайды)** — перенесено в лендинг-репо (гайды срезаны 2026-08-30; в приложении /help — только гейт) |
| **P1** | Pilot ops: staging, закрытая когорта, feedback loop; deploy-комплект: [`DEPLOY.md`](./DEPLOY.md) |
| **P1** | Onboarding Helpers; этичные ops-метрики; media/S3; secrets/backup |
| **P2** | Geo-help v2; pre-mod / AI-assist для репортов |
| **last** | **AI-помощник** — самая последняя очередь |

## Голос

1. ✅ Voice note в Dialogue
2. 🗄 STT — снято (offline-заглушки не годятся, без ключей адекватно не реализовать)
3. ✅ Translate (LLM gateway или offline marker)
4. ✅ **Кружочки** (video circles) — self-destruct при закрытии чата
5. ✅ **Голосовые с опцией удаления** (настраиваемо, per-sender)
6. 🗄 **Нативный динамический перевод** (STT → translate → TTS) — снято; остался перевод текста
7. ✅ **Live 1:1 voice в диалоге** (ADR 0021, signaling через dialogue-WS, TURN/STUN самохост); групповые rooms — по-прежнему не делаем

## Модель «облачков» (принята)

**Публично:** монолог + «Я слышу тебя» + тихие фразы (без следа) + запрос диалога.  
**Автору:** Hearer List (если есть кому писать), жест облачка на своей строке ленты, inbox запросов диалога, чат. Pulse и список облачков в UI нет (ADR 0017).

| Канал | Модерация | Видимость |
|-------|-----------|-----------|
| Silent Empathy / лучи | нет | UI снят (ADR 0018); API Pulse/hearers живы |
| Quiet Phrase | нет | жест на своей строке ленты; не список, не колокольчик |
| Moderated Cloud | ручная | то же после approve; очередь Helper |
| Dialogue | post-mod / report | 1-1 |

Инвариант: **нет** публичных комментариев, лайков и витрины реакций на странице записи.

## Фонд (ADR 0020) — готов в браузер-SPA

Некастодиальный контур: публичная казна (Squads-мультисиг, `TREASURY_SOLANA_ADDRESS` — пусто = UI скрыт), opt-in кошелёк чаевых хелпера (виден только в закрытом диалоге благодарному собеседнику, с предупреждением «отдельный кошелёк»), дежурный фонд с посуточным капом и ленивым stale-close, публичный псевдонимный отчёт `GET /v1/fund/report?period=YYYY-MM` — подписанты мультисига делят казну по нему. Деньги ходят только кошелёк → кошелёк; бэкенд не трогает ключи, платежи и RPC.
Дальше: parity фонда в Mini App (терапия там ✅), страница публичного отчёта, верификация владения подписью (phase 2).

## Терапия (ADR 0022) — зачаток

Каталог терапевтов (доступ по инвайту админа), профиль (псевдоним, подход,
языки, тариф в SOL, Solana-адрес), запрос сессии клиентом → `awaiting_payment`
→ Solana Pay QR (прямой перевод клиент → терапевт; ADR 0020 не задет) →
«Я оплатил» → **ручное подтверждение терапевта** → `paid` → 1:1 диалог и
live-звонок (ADR 0021) как канал сессии. Бэкенд хранит только статусы и
ссылки: ключей, процессинга платежей и денег на балансе нет. План:
[`VOICE_THERAPY_PLAN.md`](./VOICE_THERAPY_PLAN.md).

## Не делаем

Публичный thread, публичный who-heard, trauma map на сервере, AI как скрытый peer, open matching «всех со всеми», voice rooms до готовности notes. Словари-переводчики интерфейса как «мультиязык» — не нужны; нужен нативный динамический перевод контента.