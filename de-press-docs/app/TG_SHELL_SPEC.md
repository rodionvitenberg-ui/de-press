# TG Shell Spec — de-press app v2

> Visual/ergonomic target: **Telegram Desktop** (dark) + **web.telegram.org/a**.  
> Colors stay de-press (`hope` / `panic`). **No TG blue. No copy-paste from GPL clients.**  
> Applies to **all App Hosts** (browser, Mini App, own desktop, own mobile) — geometry and density; see [`PLATFORMS.md`](./PLATFORMS.md). On the **Telegram Mini App** host, Telegram also supplies real chrome (BackButton, themeParams, safe areas) on top of this layout.

## References (look, don't fork)

| Source | Use |
|--------|-----|
| Telegram Desktop (native) | Primary geometry |
| web.telegram.org/a | Web SPA density |
| tdesktop / telegram-tt / tweb | Structure only — **GPLv3, do not copy code** |

## Geometry (desktop)

| Token | Value | Notes |
|-------|-------|-------|
| Rail width | **72px** (`4.5rem`) | Icon-only strip |
| List width | **424px default** (280–560, resizable) | Drag handle; `localStorage` |
| Row height | **72px** (`4.5rem`) | Fixed density |
| List avatar | **54px** (`3.375rem`) | Circle |
| Header height | **56px** (`3.5rem`) | Chat / content top bar |
| Composer min | **52px** (`3.25rem`) | Bottom bar |
| Search pill height | **42px** | Inside list header |
| Bubble max-width | **70%** | of thread |
| Hit target | **≥40px** desktop | Icons 48 preferred |

## Geometry (mobile)

| Token | Value | Notes |
|-------|-------|-------|
| Phone | **≤ 759px** | List XOR detail; no rail |
| Tablet | **760–1099px** | List + main; no rail; tab bar |
| Desktop | **≥ 1100px** | Current 3-column; no tab bar |
| Tab bar | **56px** + `env(safe-area-inset-bottom)` | Лента · Чаты · Уведомления · Ещё + panic slot |
| Nested phone | `/feed/:id`, `/feed/new`, `/chat/:id` | Tab bar hidden so composer sits on the bottom inset. `/feed/mine` is a list filter. |
| Hit target | **≥44px** | `--hit-touch` |
| Inputs | **16px** | Avoid iOS focus-zoom |

## Layout

```
[ rail 72 ][ list 424 ][ main flex ]
```

- Rail: burger avatar, nav icons, panic at bottom. Tooltips = labels.
- Theme / locale / edit nav → UserMenu only.
- List: search + rows (feed monologues OR dialogues look the same).
- Main: empty | thought card | chat thread.

## States

- Row hover: `--bg-hover`
- Row active: `--bg-active` full bleed
- Soft unread: hope-tinted mini badge / dot — never hard red counter
- No “online”, no last-seen green

## Chat

- Header: avatar + title + muted subtitle (status/intent)
- Bubbles: tail radii tokens; time inside corner `tabular-nums`
- Date separator: centered chip
- Composer: circle · (mic) · pill input · send
- Typing: TG three-dots row

## Explicitly not Telegram

- Brand blue primary
- Public reactions / stories / channels
- Hard engagement counters
- Logo or wordmark of Telegram

## Acceptance checklist

1. [ ] Three columns match TG proportions
2. [ ] Rail is icon-only ~72px
3. [ ] List rows ~72px with 54px avatars
4. [ ] Search is full-width pill
5. [ ] Chat header ~56px
6. [ ] Bubbles ≤70% width with tails
7. [ ] Composer bar flush bottom
8. [ ] Empty main is centered TG-style
9. [ ] Soft badges only
10. [ ] “МНЕ ХУЕВО” always reachable on rail
