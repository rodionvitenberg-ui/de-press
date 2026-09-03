# ADR 0024: Shared theme registry package

Date: 2026-09-03
Status: accepted

## Context

`apps/browser` and `apps/mini-app` shared a *binary* dark/light split, not a
theme mechanism. Each host owned a near-twin `tokens.css`, a hardcoded
`ThemeMode = "auto" | "dark" | "light"`, a three-button switcher, and hex
literals for `<meta name="theme-color">` / Telegram chrome (`#0c0e12` /
`#f3efe9`). DESIGN_V2 promised further palettes without a refactor; the
providers and i18n could not honour that.

We needed a first extra theme — **Aurora** — carrying the `promo-depress`
landing palette (navy `#0c101b`, periwinkle muted text, teal hope) into the
app without replacing current dark/light or changing the default.

Constraints: colors only (no noise PNG, aurora image, 3D, font swap); Admin
out of scope; no root npm workspaces (same as ADR 0023); PWA is the browser
host, not a third client.

## Decision

- **One shared package, same shape as `@de-press/api-client`.**
  `packages/theme/` ships raw TS + CSS as `@de-press/theme` (exports `.` and
  `./tokens.css`); both apps depend via `file:../../packages/theme`. Hosts
  apply `data-theme` and draw the switcher from the registry; they do not
  own palettes.

- **A theme is an id + a full color-token block + a registry row.**
  `THEMES` carries `colorScheme`, `themeColor` (meta / Telegram header), and
  optional `autoAppearance`. Layout tokens (radii, TG geometry, font,
  durations) stay on `:root` and are not copied per theme.

- **Auto stays dark/light; Aurora is opt-in.** Only `dark` and `light` set
  `autoAppearance`. `autoTheme(appearance)` never returns `aurora`. OS
  `prefers-color-scheme` / Telegram `colorScheme` keep mapping to the
  existing pair so a system-dark user is not silently moved onto navy.

- **Hope in Aurora is `#5fc4aa`, not white.** The landing uses white chrome
  (links, cookie buttons, caret). In a messenger a white accent collapses
  action vs surface. Teal `#5fc4aa` (navy-pier / island moss) is the living
  color from the landing that still reads as `--accent-hope`. Panic stays
  crisis/destructive only.

- **Foreground-on-accent tokens in every theme.** `--on-accent-hope` and
  `--on-accent-panic` so filled buttons (Call, Therapy) keep contrast when
  hope is light (dark/aurora) or dark (dawn).

- **How to add a theme** (providers and switcher stay untouched):
  1. A `[data-theme="<id>"]` block covering the **full** color token set.
  2. A row in `THEMES` (`id`, `colorScheme`, `themeColor`; `autoAppearance`
     only if it should win Auto).
  3. i18n `theme.<id>` in both hosts.

## Consequences

- A fourth palette (sepia / dim / contrast) is a CSS block + a registry
  row + two i18n keys, not a second copy of tokens/providers/telegram
  fallbacks.
- Default and Auto are unchanged; Aurora never hijacks a user who did not
  pick it.
- PWA splash stays the static dark `manifest.webmanifest`; runtime chrome
  follows `<meta name="theme-color">` from the registry.
- An inline boot script in both `index.html` files applies a stored named
  theme before React, so Aurora (and Light) do not flash Dark on reload.
- Theme tests live in `apps/browser/src/core/theme.test.ts` and import the
  real package (no vitest harness inside `packages/theme`).
- Out of scope: a light Aurora twin, user-defined palettes, account-level
  sync (still `localStorage`), Admin, a dynamic PWA manifest.
