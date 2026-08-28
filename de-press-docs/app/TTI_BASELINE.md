# Browser TTI baseline (DESIGN_V2 §11.5 п.6)

Samples live in the browser `sessionStorage` key `depress:tti-samples` (never sent to the server). After a session, dump via DevTools:

```js
JSON.parse(sessionStorage.getItem("depress:tti-samples") || "[]")
```

Measure on the same machine / same data before and after P0 UI polish.

| Route | Before (ms) | After (ms) |
|---|---|---|
| `/feed` first paint | — capture on load | |
| `/feed` → `/feed/:id` | — navigate a story | |
| `/chat` → `/chat/:id` | — open a dialogue | |
| `/help` | — open help | |

Acceptance: no >20% regression on the same data after Tasks 7–10. Fill After after the P0 UI pass; leave Before as the first captured numbers in this branch.
