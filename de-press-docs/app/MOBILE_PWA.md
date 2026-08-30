# Browser mobile + installable PWA

Frozen decisions for `apps/browser`. Native Own Mobile / Mini App are out of scope.

## Layout

One Shell. `useViewportMode()` writes `document.documentElement.dataset.layout`:

| Mode | Width | Chrome |
|------|--------|--------|
| phone | ≤ 759px | Stack: list XOR detail. Tab bar. No rail. |
| tablet | 760–1099px | List + main. Tab bar. No rail. |
| desktop | ≥ 1100px | Rail + list + main. No tab bar. |

Tab bar (fixed): **Feed · Chats · Notifications · More**. Panic is the last slot, not a hideable tab.

On phone, nested `/feed/:id`, `/feed/new`, `/chat/:id` hide the tab bar so the composer can sit on the safe-area bottom. `/feed/mine` stays a list filter (tab bar visible).

`/more` holds Patterns, Help, Helper (role), Account (existing UserMenu), and the PWA install row.

## PWA

- Manifest + mint-on-dark icons + `display: standalone`
- Hand-rolled `public/sw.js` (no Workbox)
- Network-only: `/api`, `/ws`, `/media`, `/docs`, `/openapi.json`
- Cache-first hashed `/assets/*`; navigations network-first with `index.html` fallback
- Install CTA only in More. No first-visit banner
- Anti-Panic overlay is in the cached shell, so it still opens offline after the first visit
