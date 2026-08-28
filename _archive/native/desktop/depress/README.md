# de-press glue for tdesktop

C++/Qt modules that will live **next to** the tdesktop tree and be wired into the fork:

| Future pieces | Role |
|---------------|------|
| HTTP client | Talk to de-press Django API |
| Feed panel | Safe Monologue list |
| Empathy action | Silent Empathy |
| Config | API base URL, session |

Until tdesktop builds, this folder holds design notes only.

### Injection strategy (high level)

1. Add a left-column / folder entry labeled de-press (hope accent).  
2. On select, show custom widget instead of chat history.  
3. Load `GET /api/v1/stories` from configured base URL.  
4. Keep MTProto chat stack untouched for normal Telegram use.

See `../docs/BUILD.md` for binary build first.
