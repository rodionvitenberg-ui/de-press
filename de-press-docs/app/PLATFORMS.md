# Platforms of de-press

> **ADR 0016:** the experiment is **native Android first**; tdesktop **paused** (capacity).  
> **ADR 0015:** still no Web A as the product shell.  
> Browser: `apps/browser/` — a standalone web client.

---

## The essence

| # | App | Path | Role |
|---|-----|------|------|
| 1 | **Browser** | `apps/browser/` | The standalone web client of de-press |
| 2 | **Mini App** | `apps/mini-app/` | Telegram Mini App (mobile-first); the goal — the **Telegram Web A shell** |
| 3 | **Own Desktop** | later | A native wrapper (do not mix with browser) |
| 4 | **Own Mobile** | later | Our own store app (not = the Mini App only) |

```
              backend (Django)
               /            \\
    apps/browser/          apps/mini-app/
    (its own UI, no GPL)   (Web A vendor GPLv3 + de-press)
```

**Browser UI edits ≠ Mini App edits.** Only the API is shared.

## The Mini App = "an add-on to Telegram"

- Vendor: [telegram-tt / Web A](https://github.com/Ajaxy/telegram-tt) → `apps/mini-app/vendor/telegram-tt/`
- Clone: `./scripts/fetch_telegram_tt.sh`
- License: GPLv3 — [`apps/mini-app/NOTICE.GPL.md`](../../apps/mini-app/NOTICE.GPL.md)
- The impression: the familiar TG chrome/ergonomics + the de-press colors/features

Browser does **not** import Web A (otherwise copyleft covers the whole browser).

## The domain invariant

Dialogues / monologue / empathy — the **de-press backend**, not MTProto as the transport of the harbor.

## Status

| App | Status |
|-----|--------|
| Browser | ★ `apps/browser` |
| Mini App | 🟡 an interim SPA + TG bridge; the Web A vendor is cloned; the shell integration — next |
| Desktop / own mobile | ⏳ |
