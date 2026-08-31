# de-press — unified project documentation

> This folder is the **shared documentation for all repositories of the de-press project**.
> The project consists of two independent parts, each with its own repository:

| Part | Repository | Documentation |
|-------|-------------|--------------|
| **The app** (4 hosts: browser · Mini App · own desktop · own mobile) | `de-press` (this repository) | [`de-press-docs/app/`](./app/) |
| **The site / landing** (marketing, rules, "about the project") | a separate repository (the landing) | [`de-press-docs/site/`](./site/) |

## The rule

- **The landing and the app are fully separated**: their own repositories, their own stacks, their own visual engines.
- **The only connection** between them is a single transition link (from the landing into the app by a direct URL).
- **The documentation is shared**: this folder lives in the app repository but describes both repositories and is updated from both.

## Table of contents

| Section | Contents |
|--------|------------|
| [`CONTEXT.md`](./CONTEXT.md) | Domain vocabulary (terms) — shared by the site and the app |
| [`HISTORY.md`](./HISTORY.md) | Development history: how it started, every rollback and cancelled decision, the current stage |
| [`app/`](./app/) | Product documentation: **4 hosts** ([`PLATFORMS.md`](./app/PLATFORMS.md)), design, roadmap, ADR, pilot |
| [`site/`](./site/) | Everything about the landing: content, pages, the transition link |

## Related documents

- `CONTEXT.md` — the domain glossary (shared).
- Platforms (4 hosts): [`app/PLATFORMS.md`](./app/PLATFORMS.md)
- Design: [`app/DESIGN_V2.md`](./app/DESIGN_V2.md)
- Roadmap: [`app/ROADMAP.md`](./app/ROADMAP.md)
- Frontend engineering plan: [`app/FRONTEND_PLAN.md`](./app/FRONTEND_PLAN.md)
- Pilot: [`app/PILOT.md`](./app/PILOT.md)
- ADR: [`app/adr/`](./app/adr/) (including [0013 four hosts](./app/adr/0013-four-app-hosts.md))

## How to update

1. A new term → `CONTEXT.md` (no implementation details).
2. A non-trivial architectural decision → `app/adr/<NNNN>-*.md`.
3. Product changes → `app/ROADMAP.md`.
4. Design and UX → `app/DESIGN_V2.md`.
5. The landing (content/pages/transition) → `site/`.
6. The app and the landing are described together here, even though the code lives in different repositories.
