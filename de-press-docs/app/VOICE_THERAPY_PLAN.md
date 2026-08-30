# План: живой голос 1:1 (WebRTC) + терапевтический контур

Дата: 2026-08-30 · Статус: утверждён · Коммиты: (1) voice, (2) therapy

## Этап A — Live 1:1 voice (ADR 0021)

- **A1. ADR-0021** — signaling через существующий dialogue-WS; медиа P2P;
  состояние звонка in-memory на процессе daphne; ADR-0020 не задет.
- **A2. Бэкенд-сигналинг** (`apps/dialogue/calls.py` + `consumers.py`):
  - клиент → `call.ring` / `call.accept` / `call.decline` / `call.offer {sdp}` /
    `call.answer {sdp}` / `call.ice {candidate}` / `call.end`;
  - сервер → юникаст по каналам участников: `call.outgoing`, `call.incoming`,
    `call.accepted`, `call.offer`, `call.answer`, `call.ice`,
    `call.ended {reason}`; `call.busy` занятому инициатору;
  - один активный звонок на диалог и на актора; ring-timeout 45 с (сервер);
    disconnect участника = `call.ended {reason:"connection"}`; реконнект
   callee во время ringing — повторная доставка `call.incoming`;
    ICE-флуд-контроль; SDP/candidate — размерные валидаторы.
- **A3. ICE**: `GET /v1/rtc/config` (публичный) отдаёт iceServers из
  `WEBRTC_TURN_URL/USERNAME/CREDENTIAL` (самохост coturn, DEPLOY.md 8.1);
  пусто = только собственные кандидаты браузера (LAN/перцептивный NAT).
- **A4. Фронт** (`features/calls/`): чистая машина состояний `callMachine.ts`
  (vitest без WebRTC), `useCall.ts` (RTCPeerConnection, getUserMedia audio,
  mute, remote `<audio>`), `CallModal.tsx` + css; врезка в DialoguePage
  (кнопка в шапке, оверлей звонка); `useChatSocket` — passthrough
  `call.*` (onCall-callback + sendCall). Anti-Panic закрывает WS → звонок
  гаснет вместе с сигналингом (осознанно).
- **A5. i18n** `calls.*` (ru/en), тесты: vitest (машина, каталог), pytest
  (test_calls.py: ринг/акцепт/релей/деклайн/busy/disconnect).

## Этап B — Терапевтический контур (ADR 0022), зачаток

- **B1. ADR-0022**: терапевт ≠ Helper (ADR-0010 остаётся); бэкенд — только
  статусы и ссылки; платежи — прямой перевод клиент → терапевт (Solana Pay),
  подтверждение оплаты **вручную терапевтом**; ключей/процессинга нет.
- **B2. Бэкенд** `apps/therapy`: модели `TherapistProfile` (invite-токен
  от админа, псевдоним, подход, языки, тариф SOL, адрес Solana, активен),
  `TherapySession` (клиент, терапевт, статус `awaiting_payment →
  claimed → paid → active → done/declined`, цена); API:
  `GET /therapy/profiles` (публично, только активные),
  `POST /therapy/sessions` (клиент), `GET /me/therapy/*` (обе стороны),
  `POST /therapy/sessions/{id}/claim|confirm|decline|complete` (терапевт),
  админ-инвайт через Django admin; тесты.
- **B3. Фронт** `features/therapy/`: страница «Терапия» (каталог + запрос),
  кабинеты обеих сторон, модалка оплаты: Solana Pay QR (deeplink
  `solana:` + ссылка) по паттерну фонда, кнопка «Я оплатил», экран
  подтверждения у терапевта. После `paid` — 1:1 диалог + кнопка звонка
  (этап A).
- **B4. i18n** `therapy.*` (кап каталога 560 → 640 + sync flatten.test),
  PRIVACY.md, ROADMAP, PROGRESS.
