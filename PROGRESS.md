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
status: done
branch: feat/agent-a-helper-ops
notes: Help-chat message report without Story. Report.story nullable; XOR story|message; unique open help report per message×actor. Dashboard/admin tolerate null story. Did not stage Agent B files (ai/gateway.py, ai/services.py).
files: backend/apps/moderation/**, backend/api/v1/moderation.py, apps/browser/CAPABILITIES.md

## 2026-08-29  agent=A  id=A2
status: done
branch: feat/agent-a-helper-ops
notes: Dialogue Request waits for Helper (awaiting_helper) before author inbox. contract:ready GET/POST /api/v1/moderation/dialogue-requests. Left B1 WIP unstaged (ai/*, CompanionPane, memory/db.ts). client.ts also had B stream helpers in the same working tree — kept additive methods, did not revert them.
files: backend/apps/dialogue/**, backend/apps/notifications/models.py, backend/api/v1/moderation.py, ChatList.tsx, i18n helper/review, client.ts
api: GET /api/v1/moderation/dialogue-requests
api: POST /api/v1/moderation/dialogue-requests/{id}/approve
api: POST /api/v1/moderation/dialogue-requests/{id}/reject

## 2026-08-29  agent=A  id=A3
status: done
branch: feat/agent-a-helper-ops
notes: One-time Helper invite. Staff/Helper POST /api/v1/helper-invites; candidate POST …/{token}/accept with pledge. No open self-signup. Invite list UI left for A4.
files: backend/apps/identity/**, api/v1/helper_invite.py, HelperJoin.tsx, UserMenu.tsx
api: POST /api/v1/helper-invites
api: GET /api/v1/helper-invites/{token}
api: POST /api/v1/helper-invites/{token}/accept

## 2026-08-29  agent=A  id=A4
status: done
branch: feat/agent-a-helper-ops
notes: /helper tabs Облачка + Сводка (dashboard metrics, recent reports including help-chat, own invites). Help/dialogue queues stay in /chat.
files: HelperQueue.tsx, HelperQueue.module.css, helper_invite list GET
api: GET /api/v1/helper-invites

## 2026-08-29  agent=A  id=A5
status: done
branch: feat/agent-a-helper-ops
notes: Helper duty toggle. Default off. Notify+inbox Help Request and dialogue-review only when is_helper && is_on_duty && is_active. Accept/skip still allowed for is_helper. Seed helper@de-press.local on duty. New invitees stay off duty. Presence/instant match left for A6. Isolated in .worktrees/agent-a.
files: identity is_on_duty, help.py, services.py review notify, HelperQueue, UserMenu, ChatList poll gate
api: POST /api/v1/me/helper-duty
api: GET /api/v1/me + is_on_duty

## 2026-08-29  agent=A  id=A6
status: done
branch: feat/agent-a-helper-ops
notes: Instant match when an on-duty Helper has pinged within 45s (least-recent). Else A5 queue. Presence booleans only, no counts/names. Heartbeat from /chat and /helper, paused in Anti-Panic. Wait copy: at screen / on duty / nobody. No 30s promise.
files: dialogue/presence.py, help.py create, HelpWaitPane, ChatList/HelperQueue heartbeat
api: GET /api/v1/help/presence
api: POST /api/v1/help/heartbeat

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
notes: Mini App HELP parity copied (no shared package, no imports from apps/browser — verified by grep). HelpPane: human/AI path cards (POST /api/v1/help/requests → /help/wait). New HelpWaitPane: polls GET /help/requests/mine every 4s (paused in Anti-Panic), cancel, open chat or AI. New CompanionPane (/help/ai): SSE stream via api.aiSupportStream, history in IndexedDB DB v2 (companion_messages), wiped together with everything by wipeAllMemory; wipe button in CompanionPane with its own confirmation. ChatList: gray Help-inbox rows for Helpers (accept → chat, skip; pending-only; polling paused during Anti-Panic). startapp deep-links: help_wait/help-wait/wait → /help/wait, help_ai/help-ai → /help/ai; routes /help/wait and /help/ai added. helper_join deferred — A3 not in main at branch point. Build: tsc -b && vite build ok (163 modules). During the task agent A switched the shared worktree twice; B-zone edits survived checkouts and were committed on this branch with explicit pathspecs (apps/mini-app PROGRESS.md only).
files: apps/mini-app/src/core/api/types.ts, apps/mini-app/src/core/api/client.ts (append), apps/mini-app/src/core/memory/db.ts, apps/mini-app/src/core/host/startParam.ts, apps/mini-app/src/App.tsx, apps/mini-app/src/features/help/HelpPane.tsx, apps/mini-app/src/features/help/HelpPane.module.css, apps/mini-app/src/features/help/HelpWaitPane.tsx (new), apps/mini-app/src/features/help/HelpWaitPane.module.css (new), apps/mini-app/src/features/help/CompanionPane.tsx (new), apps/mini-app/src/features/help/CompanionPane.module.css (new), apps/mini-app/src/features/chat/ChatList.tsx, apps/mini-app/src/features/chat/ChatList.module.css, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, PROGRESS.md

## 2026-08-29 08:10  agent=B  id=B3
status: started
branch: feat/agent-b-companion-hosts
commit: ca2cc64
notes: Voice pipeline STT→translate→TTS. Backend (my zone): TTS adapters in apps/dialogue/speech.py (OpenAI-compatible /audio/speech, no key → get_tts()=None), thin endpoint POST /api/v1/messages/{id}/tts in api/v1/dialogue.py (ensure_transcript → translate to actor locale → synthesize; 503 = honest offline marker; translation unavailable → speaks original). Mini-app voice bubble: transcribe button + TTS "play translated" (blob playback). Browser VoiceBubble is A's zone — not touched (MAINPLAN allows API+Mini App first).
files: backend/apps/dialogue/speech.py, backend/api/v1/dialogue.py (append), backend/apps/dialogue/tests/test_speech.py, apps/mini-app/src/core/api/client.ts (append), apps/mini-app/src/features/chat/DialoguePage.tsx, apps/mini-app/src/features/chat/DialoguePage.module.css, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, PROGRESS.md
api: POST /api/v1/messages/{id}/tts → audio/mpeg | 503 {"detail":"TTS offline: no key on server"}

## 2026-08-29 08:30  agent=B  id=B3
status: done
branch: feat/agent-b-companion-hosts
notes: Voice pipeline STT→translate→TTS. Backend: TextToSpeech protocol + OpenAICompatibleTTS (/audio/speech, mp3) + get_tts() in apps/dialogue/speech.py — no key → None, never fake audio. Endpoint POST /api/v1/messages/{id}/tts (api/v1/dialogue.py, appended): ensure_transcript (STT, reuses existing) → translate_message to payload.lang (actor UI locale; if translation unavailable offline — speaks original transcript honestly) → synthesize → HttpResponse audio/mpeg; 400 not-voice/no-text, 503 = offline marker ("TTS offline: no key on server"). Mini-app voice bubble: "Расшифровать" button when no transcript (api.transcribeMessage), "Прослушать перевод" (api.messageTts → blob → Audio playback, URL revoked on ended), honest offline marker inline on 503. i18n chat.transcribe/ttsListen/ttsOffline (ru/en/types, append-only). Browser VoiceBubble/DialoguePage untouched (A's zone). Tests: DEPRESS_USE_SQLITE=1 pytest test_speech.py 6 passed (3 new TTS unit tests), test_api_chat_prefs.py 2 passed, manage.py check ok; mini-app tsc+vite build ok.
files: backend/apps/dialogue/speech.py, backend/api/v1/dialogue.py (append), backend/apps/dialogue/tests/test_speech.py, apps/mini-app/src/core/api/client.ts (append), apps/mini-app/src/features/chat/DialoguePage.tsx, apps/mini-app/src/features/chat/DialoguePage.module.css, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, PROGRESS.md
api: POST /api/v1/messages/{id}/tts → audio/mpeg | 503 {"detail":"TTS offline: no key on server"}

## 2026-08-29 08:50  agent=B  id=B4
status: done
branch: feat/agent-b-companion-hosts
notes: ADR 0019 (de-press-docs/app/adr/0019-own-mobile-vs-mini-app-desktop-tauri.md): Mini App != own mobile (stays Telegram addon); own mobile = PWA-first with explicit missing-pieces backlog (Web Push/VAPD, optional TWA store chrome, background sync) — no code; own desktop shell chosen = Tauri reusing browser build, deferred per ADR 0016 resource constraints; native/ reserved for agent B, deliberately empty (no native code shipped). Verified facts before writing: browser PWA live (manifest.webmanifest + sw.js registered in prod), native/ does not exist, previous ADR number 0018. Started+done in one commit (doc-only microtask).
files: de-press-docs/app/adr/0019-own-mobile-vs-mini-app-desktop-tauri.md (new), PROGRESS.md

## 2026-08-29  agent=A  id=merge
status: done
branch: main
notes: Local merge of feat/agent-a-helper-ops then feat/agent-b-companion-hosts. Only conflict was PROGRESS.md (concatenated; no entries dropped). client.ts and i18n auto-merged. Mini App still without A3 join / A5 duty / A6 match UI. Feature branches kept.
files: PROGRESS.md
