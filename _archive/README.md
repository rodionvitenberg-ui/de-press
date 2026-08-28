# 🗄 _archive — вынесенное из активной зоны

Папка-архив: содержимое **не входит** в активный продукт
(Browser+PWA `apps/browser/` · Mini App `apps/mini-app/` · backend `backend/`).
Ничего не удалено — всё просто собрано сюда. Позже папка целиком уйдёт в `.gitignore`.

| Путь | Что это | Почему здесь |
|------|---------|--------------|
| `legacy/next-frontend/` | Старый Next.js-фронтенд (вкл. билд `.next/`, ~800 МБ) | Архив; донор логики/типов (`de-press-docs/app/DESIGN_V2.md`) |
| `native/` | Fork Telegram Android (ADR 0016) + tdesktop (ADR 0015, был на паузе) | Вне текущего фокуса: browser + Mini App + backend |
| `AngelSlim/` | Клон стороннего тулкита сжатия LLM (Tencent AngelSlim) | Кодом не импортируется; в `PILOT.md` фигурирует только как внешняя HF-организация |

История решений сохранена в ADR (`de-press-docs/app/adr/0015`, `0016`) — они не редактировались.