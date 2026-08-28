# Приложение de-press — документация

> Репозиторий: `de-press` (backend + UI Core + будущие host-обёртки).  
> Платформа-«тихая гавань»: монологи без лайков, silent empathy, диалог только с согласия автора, Optional identity, Anti-Panic, локальные паттерны.

## Четыре направления (App Hosts)

| # | Host | Статус |
|---|------|--------|
| 1 | **Browser** — SPA `app.` | ★ ядро в `apps/web/` |
| 2 | **Telegram Mini App** — UI Core в WebView TG + Bot | ⏳ этап |
| 3 | **Own Desktop** — своё десктопное (Tauri/Electron later) | ⏳ |
| 4 | **Own Mobile** — своё мобильное (PWA → native/store) | ⏳ |

Единый source of truth: [`PLATFORMS.md`](./PLATFORMS.md) · [ADR 0013](./adr/0013-four-app-hosts.md).

**Mini App** — полноценный host и интересный этап (auth, distribution, bot notify), **не** замена own mobile/desktop.  
Диалоги и контент гавани — **всегда** на backend de-press.

## Стек (решения)

- **Backend**: Django + Ninja + Channels + PostgreSQL (системный, 5432 через `.env`) + Redis.
- **UI Core**: **Vite + React + TypeScript + CSS Modules** — чистый SPA без SSR; переиспользуется всеми hosts.
- **Browser host**: поддомен `app.` (например `app.depress.co`).
- **Mini App host**: тот же бандл + Telegram WebApp bridge (этап).
- **Own mobile / desktop**: thin native shells поверх core — после базы.
- **PWA**: мост к own mobile (P1+).
- **Компоненты v2**: ТГ-эргономика; без Tailwind; без копирования GPL tdesktop.

## Документы

| Файл | Содержание |
|------|------------|
| [`PLATFORMS.md`](./PLATFORMS.md) | **4 hosts**, shared vs host-specific, порядок этапов |
| [`MINI_APP.md`](./MINI_APP.md) | Telegram Mini App: BotFather, tunnel, auth |
| [`DESIGN_V2.md`](./DESIGN_V2.md) | Дизайн-спецификация v2.0: аксиомы, темы, ТГ-каркас |
| [`TG_SHELL_SPEC.md`](./TG_SHELL_SPEC.md) | Геометрия shell (все hosts) |
| [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) | Инженерный план фронтенда |
| [`ROADMAP.md`](./ROADMAP.md) | Версии продукта и приоритеты |
| [`PILOT.md`](./PILOT.md) | Runbook закрытого пилота |
| [`adr/`](./adr/) | Архитектурные решения (0001–0013+) |

## Структура репозитория (код)

```
de-press/
├── apps/
│   └── web/        # UI Core — Browser + Mini App (один Vite SPA)
├── backend/        # Django API + Channels
├── _archive/
│   └── legacy/next-frontend/   # 🗄 старый Next — не основной UI (вынесено)
└── de-press-docs/  # ← эта папка (документация)
```

См. также [`../../apps/README.md`](../../apps/README.md).
