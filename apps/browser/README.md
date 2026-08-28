# `@de-press/browser` — браузерное приложение

**Независимое** от Mini App. Свой код, свой UI-стек, **без** Telegram WebApp bridge и **без** GPL vendor.

## Dev

```bash
npm install
npm run dev    # http://127.0.0.1:5174
```

Backend: Daphne `:8005`.

## Граница

| Можно | Нельзя |
|-------|--------|
| Свой shell, темы, эксперименты UI | `import` из `apps/mini-app` |
| Общий backend HTTP/WS | `vendor/telegram-tt` (GPLv3) |

См. [`../README.md`](../README.md), ADR 0014.

Карта функций (что live / wired / api / local): [`CAPABILITIES.md`](./CAPABILITIES.md).
