# PROGRESS — журнал двух агентов

Читать `MAINPLAN.md` перед любой задачей. Формат записи — там же.

Не стартовать Track B, пока Gate 0 = done.

---

## 2026-08-29  agent=A  id=Gate0
status: done
branch: main (ff-merge feat/help-human-ai)
commit: 2ca15ab
notes: MAINPLAN.md + PROGRESS.md on main. Branches feat/agent-a-helper-ops and feat/agent-b-companion-hosts created from main. UI click-through of /help still for a human (no browser tools). API E2E already passed (create/accept/send/skip/cancel/AI). Agent B may start B1.
files: MAINPLAN.md, PROGRESS.md

## 2026-08-29 05:47  agent=B  id=B1
status: started
branch: feat/agent-b-companion-hosts
commit: d17f44d
notes: SSE POST /api/v1/ai/support/stream (old POST /ai/support stays) + companion IndexedDB store (DB v2) + CompanionPane streaming/wipe UI.
files: backend/apps/ai/gateway.py, backend/apps/ai/services.py, backend/api/v1/ai.py, backend/apps/ai/tests/*, apps/browser/src/core/memory/db.ts, apps/browser/src/core/api/client.ts (append only), apps/browser/src/features/help/CompanionPane.*, i18n companion.*


## 2026-08-29  agent=A  id=A1
status: started
branch: feat/agent-a-helper-ops
notes: Help-chat message report without Story.
files: backend/apps/moderation/**

## 2026-08-29  agent=B  id=B1
status: done
branch: feat/agent-b-companion-hosts
notes: SSE endpoint POST /api/v1/ai/support/stream (events meta → delta* → done, error mid-stream; headers no-cache + X-Accel-Buffering: no). Old POST /ai/support untouched; validation shared via _prepare(); crisis short-circuit sends CRISIS_REPLY_RU as a single piece (no typewriter); offline gateway streams as one chunk. Companion chat history now in IndexedDB DB v2 (store companion_messages), wiped together with everything by wipeAllMemory; wipe button in CompanionPane with its own confirmation. Shared files (client.ts, i18n ru/en/types) — only additive blocks within own sections. Tests: backend apps/ai 13 passed, browser vitest 43 passed, tsc+vite build ok.
files: backend/api/v1/ai.py, backend/apps/ai/gateway.py, backend/apps/ai/services.py, backend/apps/ai/tests/test_services.py, backend/apps/ai/tests/test_api_stream.py, apps/browser/src/core/api/client.ts, apps/browser/src/core/memory/db.ts, apps/browser/src/features/help/CompanionPane.tsx, apps/browser/src/features/help/CompanionPane.module.css, apps/browser/src/core/i18n/types.ts, apps/browser/src/core/i18n/messages/ru.ts, apps/browser/src/core/i18n/messages/en.ts, PROGRESS.md
api: POST /api/v1/ai/support/stream (SSE)

## 2026-08-29 07:05  agent=B  id=B2
status: started
branch: feat/agent-b-companion-hosts
commit: b8ac275
notes: Mini App HELP parity (apps/mini-app/** only, no imports from browser): HELP cards → create request, /help/wait, companion /help/ai (SSE + IndexedDB DB v2 + wipe), help-inbox rows in ChatList for Helpers, startapp help_wait/help_ai. helper_join skipped — A3 not in main at this branch point. Ops note: agent A switched the shared worktree to their branch mid-session and committed A3 (5c1b5be); A's uncommitted "A3 started" PROGRESS entry was stashed by B as stash@{0} ("agent A pending A3-started PROGRESS entry...") — A should pop it on feat/agent-a-helper-ops.
files: apps/mini-app/src/core/api/client.ts (append), apps/mini-app/src/core/api/types.ts, apps/mini-app/src/core/memory/db.ts, apps/mini-app/src/core/host/startParam.ts, apps/mini-app/src/App.tsx, apps/mini-app/src/features/help/*, apps/mini-app/src/features/chat/ChatList.*, apps/mini-app/src/core/i18n/*, PROGRESS.md

## 2026-08-29 07:45  agent=B  id=B2
status: done
branch: feat/agent-b-companion-hosts
notes: Mini App HELP parity copied (no shared package, no imports from apps/browser — verified by grep). HelpPane: human/AI path cards (POST /api/v1/help/requests → /help/wait). New HelpWaitPane: polls GET /help/requests/mine every 4s (paused in Anti-Panic), cancel, open chat or AI. New CompanionPane (/help/ai): SSE stream via api.aiSupportStream, history in IndexedDB DB v2 (companion_messages), wipe with window.confirm (mini-app convention, no toast lib), crisis → Anti-Panic, offline marker. ChatList: gray Help-inbox rows for Helpers (accept → chat, skip; pending-only; polling paused during Anti-Panic). startapp deep-links: help_wait/help-wait/wait → /help/wait, help_ai/help-ai → /help/ai; routes /help/wait and /help/ai added. helper_join deferred — A3 not in main at branch point. Build: tsc -b && vite build ok (163 modules). During the task agent A switched the shared worktree twice; B-zone edits survived checkouts and were committed on this branch with explicit pathspecs (apps/mini-app PROGRESS.md only).
files: apps/mini-app/src/core/api/types.ts, apps/mini-app/src/core/api/client.ts (append), apps/mini-app/src/core/memory/db.ts, apps/mini-app/src/core/host/startParam.ts, apps/mini-app/src/App.tsx, apps/mini-app/src/features/help/HelpPane.tsx, apps/mini-app/src/features/help/HelpPane.module.css, apps/mini-app/src/features/help/HelpWaitPane.tsx (new), apps/mini-app/src/features/help/HelpWaitPane.module.css (new), apps/mini-app/src/features/help/CompanionPane.tsx (new), apps/mini-app/src/features/help/CompanionPane.module.css (new), apps/mini-app/src/features/chat/ChatList.tsx, apps/mini-app/src/features/chat/ChatList.module.css, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, PROGRESS.md

