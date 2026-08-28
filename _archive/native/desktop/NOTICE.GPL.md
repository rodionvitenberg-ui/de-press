# GPLv3 — Telegram Desktop fork

This directory targets a **derivative work** of Telegram Desktop
([telegramdesktop/tdesktop](https://github.com/telegramdesktop/tdesktop)),
licensed under the **GNU General Public License v3** (with OpenSSL exception as upstream).

## Obligations when distributing our desktop client

1. Ship **corresponding source** of the full client (tdesktop + our patches/`depress/`).  
2. Keep license notices.  
3. Do **not** link this code into `apps/browser` (keep browser a separate non-derivative program).

Backend (`backend/`) and browser SPA remain separate programs communicating over network APIs.
