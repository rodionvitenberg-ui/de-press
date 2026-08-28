# de-press Desktop — fork of Telegram Desktop (tdesktop)

Нативный desktop-клиент: **реальный tdesktop UI** + раздел de-press (наш API).

| | |
|--|--|
| Upstream | https://github.com/telegramdesktop/tdesktop |
| License | **GPLv3** (see `NOTICE.GPL.md`) |
| Build | Linux via **Docker** (official) |
| Clone dir | `tdesktop/` (gitignored — run fetch script) |

## Layout

```
native/desktop/
  README.md
  NOTICE.GPL.md
  docs/BUILD.md
  scripts/
    fetch_tdesktop.sh
    build_linux_docker.sh
  depress/                 # our C++/Qt glue (grows with integration)
  tdesktop/                # upstream clone (not committed; ~GB)
```

## Quick start

1. **API credentials** (required to talk to Telegram servers for MTProto login):  
   https://core.telegram.org/api/obtaining_api_id → `api_id` + `api_hash`

2. **Clone** (long, recursive submodules):

```bash
./scripts/fetch_tdesktop.sh
```

3. **Prepare + build** (Docker; needs free disk/RAM — see docs/BUILD.md):

```bash
export TDESKTOP_API_ID=...
export TDESKTOP_API_HASH=...
./scripts/build_linux_docker.sh
```

4. Binary lands under `tdesktop/out/` (per upstream layout).

## de-press integration (roadmap)

1. ✅ Scaffold + ADR  
2. ⏳ Vanilla tdesktop builds and runs  
3. ⏳ UI entry «de-press» in left column  
4. ⏳ Panel: `GET /api/v1/stories` + empathy  
5. ⏳ Point API to local Daphne `:8005`

Do **not** copy tdesktop sources into `apps/browser`.
