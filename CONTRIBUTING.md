# Contributing to de-press

Thank you for considering a contribution. de-press is a non-profit "quiet harbor"
platform for people in distress. Before anything else, read the domain rules in
[`CONTEXT.md`](./CONTEXT.md) and the privacy promises in [`PRIVACY.md`](./PRIVACY.md):
they are product invariants, not suggestions.

## How to contribute

1. **Ask before large changes.** For anything beyond a bug fix, open an issue and
   describe the problem and the approach first. The project has strong domain
   constraints (no public likes/comments, ZK patterns on-device, AI never a hidden
   peer, no toxic positivity) — a change that fights them will not be merged.
2. **Find the right place.** The repository is a monorepo:
   - `backend/` — Django + Ninja + Channels (REST, WebSockets, Celery tasks);
   - `apps/browser/`, `apps/mini-app/`, `apps/admin/` — three independent Vite + React SPA;
   - `packages/` — shared `@de-press/theme` (design tokens) and `@de-press/api-client`.
   Never import `apps/mini-app/vendor/**` (GPLv3) into the browser or backend.
3. **Open a PR** against `main` with a clear description and a filled checklist.

## Development setup

See the README, section *Running the project (locally)* — backend needs Python 3.12+,
PostgreSQL and Redis; the frontends need Node 20+.

Quick orientation:

```bash
# Backend (from backend/)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/local.txt
python manage.py migrate --noinput
python manage.py seed_local      # demo data + login, see README
daphne -b 127.0.0.1 -p 8005 config.asgi:application

# Frontends (each app independently)
cd apps/browser && npm install && npm run dev     # :5174
cd apps/mini-app && npm install && npm run dev    # :5175
```

## Tests & checks

Run the checks that cover your change before opening a PR:

```bash
# Backend
cd backend
DEPRESS_USE_SQLITE=1 CHANNEL_LAYER=memory pytest -q

# Frontend (per app with a test suite: browser, mini-app)
npm test          # vitest run
npm run build     # tsc -b && vite build (type check + production build)
```

A PR is expected to pass: backend `pytest`, `vitest` for touched apps, and
`npm run build` in every app you changed.

## Commit conventions

- One logical change per commit.
- Conventional Commits style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`,
  `chore:` with an optional scope, e.g. `fix(dialogue): drop stale unread badge`.
- Sign every commit with the Developer Certificate of Origin:

```bash
git commit -s
```

Your commit must end with:

```
Signed-off-by: Your Name <your.email@example.com>
```

By adding this trailer you certify that you wrote the change or have the right to
pass it on under the project license (see the [DCO](https://developercertificate.org/)
text). Commits without it will be rejected.

## Licensing

- The repository is licensed **AGPL-3.0-or-later** (see [`LICENSE`](./LICENSE)). Your
  contributions are accepted under the same license.
- `apps/mini-app/vendor/telegram-tt/` is GPLv3 third-party code, fetched by
  `scripts/fetch_telegram_tt.sh` at a pinned revision — never committed, never copied
  into the browser or backend. See [`apps/mini-app/NOTICE.GPL.md`](./apps/mini-app/NOTICE.GPL.md).
- Do not add code that would force a license change, and do not copy GPLv3 code into
  the AGPL tracks.

## Code of Conduct

Participation in this project is governed by our
[Code of Conduct](./CODE_OF_CONDUCT.md). Be humane; this project exists for people
who are struggling.
