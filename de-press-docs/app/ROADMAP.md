# Roadmap de-press.co

См. также [README.md](../README.md) (стадия и приоритеты), [CONTEXT.md](../CONTEXT.md), [PILOT.md](./PILOT.md).

## Стадия (2026-08)

**Product core v0.0–v0.14 закрыт в коде.**  
**P1 «Soft-notify» закрыт** (включая `/inbox` по magic-token и `PUBLIC_BASE_URL` в settings).  
**Browser host (UI Core v2)** — Vite SPA с ТГ-эргономикой: каркас + дожим P0 закрыт.  
**Кружочки + voice retention на сервере закрыты.**  
Дальше по продукту: **нативный динамический мультиязык** (P1).  
По hosts: **Telegram Mini App** (этап), затем/параллельно **own mobile** и **own desktop**.  
**AI-помощник — в самую последнюю очередь.**

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
| **v0.14** | Voice notes + STT + translate | ✅ |
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
| **P1** | **Нативный динамический мультиязык**: STT → translate → TTS (контент, не словари UI) |
| **P1** | **Telegram Mini App host (этап)**: Bot + Mini App, initData auth, theme bridge, optional bot soft-notify; диалоги остаются на de-press backend — **не** замена own mobile |
| **P1** | **Own Mobile**: ТГ-таб-бар layout → PWA / нативная обёртка / store (отдельный host) |
| **P1** | **Own Desktop**: обёртка UI Core (Tauri / Electron — решение позже) |
| **P1 🟡** | **PWA bridge on browser host** — installable standalone + phone/tablet chrome; native store still later. See [`MOBILE_PWA.md`](./MOBILE_PWA.md) |
| **P1** | Публичные страницы (помощь, гайды) — через интерфейс приложения / лендинг |
| **P1** | Pilot ops: staging, закрытая когорта, feedback loop |
| **P1** | Onboarding Helpers; этичные ops-метрики; media/S3; secrets/backup |
| **P2** | Geo-help v2; pre-mod / AI-assist для репортов |
| **last** | **AI-помощник** — самая последняя очередь |

## Голос

1. ✅ Voice note в Dialogue
2. ✅ STT (Whisper-compatible или offline)
3. ✅ Translate (LLM gateway или offline marker)
4. ✅ **Кружочки** (video circles) — self-destruct при закрытии чата
5. ✅ **Голосовые с опцией удаления** (настраиваемо, per-sender)
6. 🔜 **Нативный динамический перевод** (STT → translate → TTS) — обязателен для межъязыкового общения
7. Live voice rooms — v1.x после trust + mod

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

## Не делаем

Публичный thread, публичный who-heard, trauma map на сервере, AI как скрытый peer, open matching «всех со всеми», voice rooms до готовности notes. Словари-переводчики интерфейса как «мультиязык» — не нужны; нужен нативный динамический перевод контента.