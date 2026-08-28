# de-press × tdesktop — injection map

After vanilla tdesktop builds, we wire a **custom section** without rewriting MTProto.

## Likely hook points (upstream SourceFiles)

| Area | Path | Why |
|------|------|-----|
| Left column / dialogs list | `dialogs/dialogs_widget.{h,cpp}` | Natural place for a sticky “de-press” row / filter |
| Section framework | `window/section_widget.{h,cpp}`, `window/section_memento.h` | Custom main column content |
| Filters / folders | `data/data_chat_filters.*`, filter UI | Optional “folder-like” entry |
| Main window chrome | `window/main_window.*` | Menu / title actions (Anti-Panic later) |
| Session | `main/main_session.*` | Lifetime; do **not** overload with haven state |

## Minimal product surface (v0)

1. **Entry:** one list row “de-press” / “Тихая гавань” at top of dialogs (or under filters).  
2. **Main:** `DepressSectionWidget` — list of stories from `GET /api/v1/stories`.  
3. **Action:** button → `POST /api/v1/stories/{id}/empathy`.  
4. **Config:** settings string `depress.apiBase` default `http://127.0.0.1:8005`.

## Code layout (ours)

```
native/desktop/depress/
  INTEGRATION.md          ← this file
  README.md
  # planned:
  # api/depress_client.{h,cpp}   Qt Network
  # ui/depress_section.{h,cpp}
  # ui/depress_feed.{h,cpp}
```

Patches against `tdesktop/` will be git commits on a branch `depress/native-desktop` (local, not force-pushed to upstream).

## Build gate

No UI patch lands until:

```text
docker image: tdesktop:centos_env
binary:       tdesktop/out/.../Telegram  (or equivalent)
```

## Auth v0

Reuse de-press session: login via email/password against `/api/v1/auth/login`, store cookie/token in Qt settings. MTProto login remains for real TG chats.
