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

## 2026-08-29 08:14  agent=A  id=A2-A6-miniapp
status: done
branch: main
notes: Mini App browser parity for Track A helper ops (no imports from apps/browser — verified by grep). API: types (Me.is_staff/is_on_duty, HelpPresence, HelperInvite, NotificationKind += dialogue_request_review) + client endpoints (helpPresence, helperHeartbeat, dialogueReviewInbox, approve/rejectDialogueReview, create/list/get/acceptHelperInvite, setHelperDuty). i18n: helper.review*/invite*/join*/tab*/duty*, help.waitMatchedTitle/waitPresence*, notifications.kind.dialogue_request_review (en/ru/types). ChatList: duty-gated review inbox (awaiting_helper, 20s), heartbeat via useHelperHeartbeat(isHelper) — browser contract (single enabled arg, useAntiPanic inside), review blocks with approve/reject. HelperQueue: clouds/summary tabs, duty card+toggle, dashboard metrics/reports, invites list. HelperJoin.tsx (new): /helper/join (token preview, pledge, accept) + /helper/invite (create link); routes wired; start_param helper_join_<uuid> → /helper/join?token= (startParam.ts). UserMenu: duty toggle (is_helper) + invite link (is_helper|is_staff). HelpWaitPane: presence line (helpPresence poll 4s, Anti-Panic paused) + waitMatchedTitle. Backend: stale test fix — test_websocket_receives_live_notification used kind "message" which is inbox-hidden by design (chat unread lives on the dialogue list, _INBOX_HIDDEN since 99723a4), so unread_count event was 0; switched to "dialogue_request" (counted kind). Verify: mini-app tsc -b + vite build ok; browser tsc -b ok + vitest 8 files / 43 tests passed; backend apps/notifications 18 passed. Uncommitted foreign-zone edits (browser StoryPage/i18n, backend support) left untouched.
files: apps/mini-app/src/core/api/types.ts, apps/mini-app/src/core/api/client.ts, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/en.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/host/startParam.ts, apps/mini-app/src/App.tsx, apps/mini-app/src/components/layout/UserMenu.tsx, apps/mini-app/src/features/chat/ChatList.tsx, apps/mini-app/src/features/help/HelpWaitPane.tsx, apps/mini-app/src/features/helper/HelperQueue.tsx, apps/mini-app/src/features/helper/HelperQueue.module.css, apps/mini-app/src/features/helper/HelperJoin.tsx (new), apps/mini-app/src/features/helper/HelperJoin.module.css (new), apps/mini-app/src/features/helper/useHelperHeartbeat.ts (new), backend/apps/notifications/tests/test_consumers.py, PROGRESS.md

## 2026-08-29 22:24  agent=human  id=A2-rollback
status: done
branch: main
notes: Rolled back A2 helper pre-moderation of Dialogue Requests — requests now go straight to the author. create_request always PENDING, review notify removed; legacy review inbox/approve/reject endpoints kept (old notifications/data still render, new requests skip the gate). Migration 0012 maps awaiting_helper → pending. Review inbox UI removed from browser+mini-app ChatList; dead client methods (dialogueReviewInbox/approve/reject) removed; apps/mini-app/dist/ gitignored. Verified: backend full suite 100% no F/E + test_dialogue_review 2 passed; browser tsc + vitest 43/43; mini-app tsc.
files: backend/apps/dialogue/models.py, backend/apps/dialogue/services.py, backend/apps/dialogue/migrations/0012_release_awaiting_helper.py (new), backend/apps/dialogue/tests/helpers.py, backend/apps/dialogue/tests/test_dialogue_review.py, backend/apps/identity/models.py, apps/browser/src/components/layout/UserMenu.tsx, apps/browser/src/core/hooks/useNotifications.ts, apps/browser/src/core/i18n/messages/ru.ts, apps/browser/src/core/i18n/messages/en.ts, apps/browser/src/features/chat/ChatList.tsx, apps/browser/src/features/helper/HelperQueue.tsx, apps/browser/src/core/api/client.ts, apps/mini-app/src/components/layout/UserMenu.tsx, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, apps/mini-app/src/features/chat/ChatList.tsx, apps/mini-app/src/features/helper/HelperQueue.tsx, apps/mini-app/src/core/api/client.ts, .gitignore, PROGRESS.md

## 2026-08-29  agent=human  id=voice-stt-tts-rollback
status: done
branch: main
notes: Rolled back the voice STT→translate→TTS pipeline (user decision: not needed for now, cannot be implemented adequately without keys). Removed: auto-STT on voice send (dialogue voice notes + story voice monologues/comments), ensure_transcript, POST /messages/{id}/transcribe, POST /messages/{id}/tts (B3), STT/TTS adapters + get_stt/get_tts in speech.py (translator stack kept), STT_* settings, mini-app transcribeMessage/messageTts clients, voice-bubble buttons (Расшифровать/Прослушать перевод) + ttsBusy/ttsError state + i18n chat.transcribe/ttsListen/ttsOffline (en/ru/types) + .voiceActions/.ttsOffline CSS + ChatMessage.transcript type field. translate_message now refuses transcript-less voice messages ("Нечего переводить") instead of translating the "[голосовое сообщение]" placeholder; mini-app «Перевод» action hidden for voice bubbles (browser menu was already text-only). Text-message translate + UI-catalog translation (apps/common/i18n_ui.py) untouched. DB fields transcript/translations/source_lang kept (legacy data, no migration); old transcripts still render via display_text. Docs: README (features/stack/env/priorities), ROADMAP (v0.14 row, P1 row → снято, Голос items 2/6), .env.example. Tests updated: test_speech.py keeps 3 translator tests (3 TTS tests dropped), voice tests now assert no transcript. Verify: manage.py check ok; DEPRESS_USE_SQLITE=1 pytest test_speech.py+test_services.py+test_api_chat_prefs.py+stories/test_services.py → 37 passed (full dialogue dir exceeds 30s cmd timeout — env known); mini-app tsc -b + vite build ok; browser tsc -b ok; repo grep: no STT/TTS/transcribe leftovers in code.
files: backend/apps/dialogue/speech.py, backend/apps/dialogue/services.py, backend/api/v1/dialogue.py, backend/config/settings/base.py, backend/apps/stories/services.py, backend/apps/dialogue/tests/test_speech.py, backend/apps/dialogue/tests/test_services.py, backend/apps/stories/tests/test_services.py, apps/mini-app/src/core/api/client.ts, apps/mini-app/src/core/api/types.ts, apps/mini-app/src/core/hooks/useChatSocket.ts, apps/mini-app/src/features/chat/DialoguePage.tsx, apps/mini-app/src/features/chat/DialoguePage.module.css, apps/mini-app/src/core/i18n/types.ts, apps/mini-app/src/core/i18n/messages/ru.ts, apps/mini-app/src/core/i18n/messages/en.ts, README.md, de-press-docs/app/ROADMAP.md, .env.example, PROGRESS.md

## 2026-08-29  agent=human  id=frontend-hardening
status: done
branch: main
notes: Design-polish pass, Этап A (skill impeccable-design-polish, audit mode). Project run: daphne :8005 + browser vite :5174 + mini-app vite :5175; vitest 43/43; mini-app tsc+vite build ok; sw.js node --check ok. Fixes: (1) browser sw.js — navigate branch does not cache non-ok responses anymore (a 500 could previously poison the offline shell); (2) mini-app base.css — overscroll-behavior none, iOS zoom guard (pointer:coarse → input/textarea/select 16px), body.antiPanicActive overflow lock (useAntiPanic toggled the class but the CSS rule was missing); (3) mini-app index.html — viewport meta + interactive-widget=resizes-content (parity with browser host). Deferred deliberately: TG viewportStableHeight pinning — blind pinning risks hiding the composer behind the Android keyboard (webview resize is already handled by the height:100% chain); needs live TG QA via tunnel in Этап B. Audit notes: PWA on browser host is complete per MOBILE_PWA.md (manifest, icons, sw strategies, install row in More, PROD-only registration); tokens/base drift between hosts — keep fixes in sync on both sides; aria 118/96; safe-area browser-only (ok for TG host until live QA says otherwise).
files: apps/browser/public/sw.js, apps/mini-app/src/styles/base.css, apps/mini-app/index.html, PROGRESS.md

## 2026-08-29  agent=human  id=help-page-split
status: done
branch: main
notes: Reworked /help for browser host per user request. (1) Help journey routes (/help, /help/wait, /help/ai) render via new HelpChrome wrapper: full-bleed on desktop (>1099px, no rail/tab, own main + AntiPanicOverlay), regular Shell with TabBar on phone/tablet so mobile UX is unchanged. (2) /help is now a full-page gate with two halves: left = AI promo (tag/title/lead + Link to /help/ai), right = human helper — one click (whole half via stretched CTA on desktop) creates a HelpRequest and navigates to /help/wait (existing pipeline: 4s poll of my-help-request + presence line → helper accepts in HelperQueue → dialogue opens in chat). Optional note textarea stays phone/tablet-only. Crisis orienters, resources, safety and guides kept below the fold. (3) /help/ai now spans full page width; inner column capped at 56rem for readability; back button added. i18n: added common.back, help.aiTag, help.humanTag (ru/en/types). Mini-app untouched (phone-only). Helper dashboard design deferred (user: "это потом"). Verify: tsc -b ok, vitest 43/43, vite build ok; services restarted after session resume (daphne :8005, vite :5174/:5175).
files: apps/browser/src/App.tsx, apps/browser/src/App.module.css, apps/browser/src/features/help/HelpPane.tsx, apps/browser/src/features/help/HelpPane.module.css, apps/browser/src/features/help/CompanionPane.tsx, apps/browser/src/features/help/CompanionPane.module.css, apps/browser/src/features/help/HelpWaitPane.module.css, apps/browser/src/core/i18n/types.ts, apps/browser/src/core/i18n/messages/ru.ts, apps/browser/src/core/i18n/messages/en.ts, PROGRESS.md

## 2026-08-30  agent=human  id=chat-unread-autoread
status: done
branch: main
notes: Fixed stale unread badge on the currently open chat. Root cause: DialoguePage called POST /dialogues/{id}/mark-read only once per dialogue switch; incoming messages arriving while the window was hidden/minimized raised server unread_count, background ChatList poll was paused (refetchIntervalInBackground=false), and on refocus refetchOnWindowFocus delivered a fresh unread_count for the open dialogue — badge persisted until the user switched chats. Fix in DialoguePage: markRead is now a deduped callback (in-flight ref) invoked (1) on dialogue open/switch (previous behavior), (2) when a peer message lands while the page is visible (lastReadMarked ref keyed by message id prevents repeat POSTs from the 4s HTTP-fallback poll), (3) on visibilitychange→visible and window focus with the chat open — badge drops on return. Invalidates ["dialogues"] each time so ChatList/TabBar/Sidebar badges clear immediately. Verify: tsc -b ok, vitest 43/43, vite build ok.
files: apps/browser/src/features/chat/DialoguePage.tsx, PROGRESS.md
