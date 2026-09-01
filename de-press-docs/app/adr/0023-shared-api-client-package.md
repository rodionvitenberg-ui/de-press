# ADR 0023: Shared API client package for browser and mini-app

Date: 2026-09-01
Status: accepted

## Context

`apps/browser` and `apps/mini-app` talk to the same Django Ninja backend and
carried two near-twin hand-written API clients (`src/core/api/client.ts` +
`types.ts` each, ~1,600 lines total). They were synced manually and had
already drifted: `loginTelegram` and `testTelegramDigest` existed only in
mini-app, while pins/mutes/forward/edit/delete/reopen dialogue endpoints,
`publishStoryVoice` and several type fields (`SupportCloud.image_url`,
`ChatMessage.reply_to`, wider `NotificationKind`) existed only in browser.
The audit (Q3) flagged this duplication.

Constraints: the repo has no root `package.json` (no npm workspaces); both
apps build with `tsc -b && vite build` and test with vitest; CI is absent.

## Decision

- **One shared package, no workspace machinery.** `packages/api-client/`
  ships raw TS source as `@de-press/api-client` (exports `.` and `./types`);
  both apps depend on it via `file:../../packages/api-client`. npm symlinks
  it, so each app's `tsc`/`vite`/`vitest` compile it directly — no build
  step, no root lockfile, no restructuring.
- **Hand-written transport, hand-written types — once.** The request
  wrapper (same-origin + `credentials: "include"`), `ApiError`, SSE streaming
  for AI support and the voice-upload helper stay handwritten (multipart,
  streaming and cookie semantics are not covered usefully by codegen). The
  `api` object is the union of both former clients: every frontend now
  simply has endpoints it doesn't call yet.
- **Apps keep their import surface.** `apps/*/src/core/api/client.ts` and
  `types.ts` became one-line re-export shims, so the 72 existing import
  sites across components/tests stayed untouched.
- **Type conflicts resolve to the wider option** (`Dialogue.story_id:
  string | null`, 12-variant `NotificationKind`, optional cloud/media
  fields): the union describes what the single backend actually returns.
- **Codegen pipeline, phased adoption.** `npm run gen:api` in the package
  runs `openapi-typescript` against Django's `/api/openapi.json` and writes
  `src/schema.gen.d.ts` (committed; schema verified: 105 paths, 85 named
  schemas). Hand-written types remain the compile-time contract for now;
  migrating interfaces onto `components["schemas"][...]` references is a
  deliberate follow-up, not done inline.

## Consequences

- Client drift between frontends is structurally impossible; a new backend
  endpoint is added in exactly one place.
- Endpoints unused by a given app are still bundled (single `api` object;
  measured cost is a few KB pre-gzip) — accepted for simplicity.
- `npm install` must run per app (file: dep), as before per-app lockfiles.
- Backend↔client type sync is still manual until the `schema.gen.d.ts`
  migration lands; `npm run gen:api` makes the diff reviewable at any time.
