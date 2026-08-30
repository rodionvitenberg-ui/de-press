# The de-press app — documentation

> Repository: `de-press` (backend + UI Core + the future host wrappers).  
> The "quiet harbor" platform: monologues without likes, silent empathy, a dialogue only with the author's consent, optional identity, Anti-Panic, local patterns.

## The four directions (App Hosts)

| # | Host | Status |
|---|------|--------|
| 1 | **Browser** — the SPA `app.` | ★ the core in `apps/web/` |
| 2 | **Telegram Mini App** — UI Core in the TG WebView + a Bot | ⏳ a stage |
| 3 | **Own Desktop** — our own desktop (Tauri/Electron later) | ⏳ |
| 4 | **Own Mobile** — our own mobile (PWA → native/store) | ⏳ |

The single source of truth: [`PLATFORMS.md`](./PLATFORMS.md) · [ADR 0013](./adr/0013-four-app-hosts.md).

**The Mini App** is a full host and an interesting stage (auth, distribution, bot notify), **not** a replacement for own mobile/desktop.  
The dialogues and the harbor content are **always** on the de-press backend.

## The stack (decisions)

- **Backend**: Django + Ninja + Channels + PostgreSQL (system, 5432 via `.env`) + Redis.
- **UI Core**: **Vite + React + TypeScript + CSS Modules** — a pure SPA without SSR; reused by all hosts.
- **The browser host**: the `app.` subdomain (for example `app.depress.co`).
- **The Mini App host**: the same bundle + a Telegram WebApp bridge (a stage).
- **Own mobile / desktop**: thin native shells over the core — after the base.
- **PWA**: a bridge to own mobile (P1+).
- **The v2 components**: TG ergonomics; no Tailwind; no copying of the GPL tdesktop.

## Documents

| File | Content |
|------|---------|
| [`PLATFORMS.md`](./PLATFORMS.md) | **4 hosts**, shared vs host-specific, the stage order |
| [`MINI_APP.md`](./MINI_APP.md) | Telegram Mini App: BotFather, a tunnel, auth |
| [`DESIGN_V2.md`](./DESIGN_V2.md) | The design spec v2.0: axioms, themes, the TG skeleton |
| [`TG_SHELL_SPEC.md`](./TG_SHELL_SPEC.md) | The shell geometry (all hosts) |
| [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) | The frontend engineering plan |
| [`ROADMAP.md`](./ROADMAP.md) | The product versions and priorities |
| [`PILOT.md`](./PILOT.md) | The closed pilot runbook |
| [`adr/`](./adr/) | Architecture decisions (0001–0013+) |

## The repository structure (code)

```
de-press/
├── apps/
│   └── web/        # UI Core — Browser + Mini App (one Vite SPA)
├── backend/        # Django API + Channels
├── _archive/
│   └── legacy/next-frontend/   # 🗄 the old Next — not the main UI (moved out)
└── de-press-docs/  # ← this folder (the documentation)
```

See also [`../../apps/README.md`](../../apps/README.md).
