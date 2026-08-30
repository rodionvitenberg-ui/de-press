# Anti-Panic (the silence mode)

"I'm not ok" — the stop button. One shared `AntiPanicProvider`. Do not confuse with the Mini App.

## Behavior

- **Enter** (rail / tab bar / Help): severing all WS, pausing `audio`/`video`, the 4–7–8 + 5–4–3–2–1 overlay.
- **While active:** `useFeedSocket` / `useChatSocket` / `useNotifications` are off (`enabled=false`) — no reconnect and no HTTP-poll toasts.
- **Exit:** the "Leave the mode" button only. Escape does not close it.
- **Persist:** `localStorage depress_anti_panic=1`. A reload keeps the overlay.

## Not in this pass

An AI step, a local "scream into text", a server flag.
