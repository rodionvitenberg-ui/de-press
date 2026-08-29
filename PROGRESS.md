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
