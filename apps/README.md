# Client applications (`apps/`)

> Не путать с `backend/apps/` (Django).

## Главное требование

**Browser и Mini App — два отдельных приложения.**  
Правки интерфейса в одном **не** попадают в другое автоматически.

| App | Path | Port (dev) | Назначение |
|-----|------|------------|------------|
| **Browser** | [`browser/`](./browser/) | **5174** | Самостоятельный веб-клиент de-press |
| **Mini App** | [`mini-app/`](./mini-app/) | **5175** | Telegram Mini App (mobile-first); цель — оболочка **Telegram Web A** |

```
apps/
  browser/                 # независимое браузерное приложение
  mini-app/                # независимое Mini App
    vendor/telegram-tt/    # Telegram Web A (GPLv3) — см. NOTICE.GPL.md
    src/                   # de-press интеграция / interim SPA
```

## Product shell = native Telegram (не web)

Целевое впечатление «аддон к Телеге» реализуется **нативными** клиентами:

- **Desktop:** [`../_archive/native/desktop/`](../_archive/native/desktop/) — fork **tdesktop** (ADR 0015) — вынесено в архив
- **Mobile:** [`../_archive/native/android/`](../_archive/native/android/) (ADR 0016) — вынесено в архив; `native/ios` — later
- **Mini App / Web A** — **не** product shell; optional side track only

Browser остаётся отдельным веб-приложением без кода tdesktop.

## Backend

Общий: `backend/` (Django). Диалоги/stories всегда на de-press API, не MTProto.

## Dev

```bash
# Browser only
cd apps/browser && npm run dev    # :5174

# Mini App only (interim SPA + TG bridge)
cd apps/mini-app && npm run dev   # :5175

# Fetch Web A sources (large)
./scripts/fetch_telegram_tt.sh
```
