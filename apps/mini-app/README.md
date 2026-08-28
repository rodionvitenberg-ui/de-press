# `@de-press/mini-app` — Telegram Mini App

**Отдельное** приложение (не symlink browser). Mobile-first; desktop WebView — вторично.

## Цель UX

«Открыл Телегу → de-press как аддон»: **фактическая оболочка Telegram Web A**, свои акценты и функции.

## Структура

| Path | Роль |
|------|------|
| `src/` | Сейчас: interim de-press SPA + `Telegram.WebApp` host (auth, startapp, BackButton) |
| `vendor/telegram-tt/` | **Telegram Web A** (GPLv3) — клон Web A для оболочки |
| `NOTICE.GPL.md` | Copyleft obligations |

```bash
# vendor (large ~400MB+)
../../scripts/fetch_telegram_tt.sh

npm install
npm run dev    # http://127.0.0.1:5175  — tunnel HTTPS → BotFather Mini App URL
```

## Дорожная карта оболочки

1. ✅ Отдельная папка от browser  
2. ✅ Vendor Web A в `vendor/telegram-tt`  
3. ⏳ Сборка Web A / theme tokens de-press (`hope` / `panic`)  
4. ⏳ Замена interim SPA: списки/чат Web A → данные de-press API  
5. ⏳ Публикация Mini App под GPLv3  

Browser **никогда** не линкуется с этим vendor.

## Backend

Тот же de-press API (`/auth/telegram`, stories, dialogue WS). MTProto Web A — для «ощущения» chrome; транспорт гавани остаётся нашим.
