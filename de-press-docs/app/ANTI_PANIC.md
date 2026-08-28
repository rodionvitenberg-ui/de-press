# Anti-Panic (режим тишины)

«Мне хуево» — стоп-кнопка. Один общий `AntiPanicProvider`. Не путать с Mini App.

## Поведение

- **Enter** (rail / tab bar / Help): обрыв всех WS, пауза `audio`/`video`, оверлей 4–7–8 + 5–4–3–2–1.
- **Пока активен:** `useFeedSocket` / `useChatSocket` / `useNotifications` выключены (`enabled=false`) — нет reconnect и HTTP poll тостов.
- **Exit:** только кнопка «Выйти из режима». Escape не закрывает.
- **Persist:** `localStorage depress_anti_panic=1`. Reload оставляет оверлей.

## Не в этом проходе

ИИ-шаг, локальный «поорать в текст», серверный флаг.
