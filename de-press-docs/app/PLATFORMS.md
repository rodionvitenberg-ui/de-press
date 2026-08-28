# Платформы de-press

> **ADR 0016:** experiment **native Android first**; tdesktop **paused** (capacity).  
> **ADR 0015:** still no Web A as product shell.  
> Browser: `apps/browser/` — отдельный веб-клиент.

---

## Суть

| # | Приложение | Path | Роль |
|---|------------|------|------|
| 1 | **Browser** | `apps/browser/` | Самостоятельный веб-клиент de-press |
| 2 | **Mini App** | `apps/mini-app/` | Telegram Mini App (mobile-first); цель — **оболочка Telegram Web A** |
| 3 | **Own Desktop** | later | Нативная обёртка (не смешивать с browser) |
| 4 | **Own Mobile** | later | Своё store-приложение (не = только Mini App) |

```
              backend (Django)
               /            \
    apps/browser/          apps/mini-app/
    (свой UI, без GPL)     (Web A vendor GPLv3 + de-press)
```

**Правки UI browser ≠ правки Mini App.** Общий только API.

## Mini App = «аддон к Телеге»

- Vendor: [telegram-tt / Web A](https://github.com/Ajaxy/telegram-tt) → `apps/mini-app/vendor/telegram-tt/`
- Клон: `./scripts/fetch_telegram_tt.sh`
- Лицензия: GPLv3 — [`apps/mini-app/NOTICE.GPL.md`](../../apps/mini-app/NOTICE.GPL.md)
- Впечатление: привычный TG chrome/эргономика + цвета/функции de-press

Browser **не** импортирует Web A (иначе copyleft на весь browser).

## Инвариант домена

Диалоги / monologue / empathy — **backend de-press**, не MTProto как транспорт гавани.

## Статус

| App | Статус |
|-----|--------|
| Browser | ★ `apps/browser` |
| Mini App | 🟡 interim SPA + TG bridge; Web A vendor склонирован; интеграция оболочки — next |
| Desktop / own mobile | ⏳ |
