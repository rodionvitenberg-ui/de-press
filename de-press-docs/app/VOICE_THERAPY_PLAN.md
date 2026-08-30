# Plan: live 1:1 voice (WebRTC) + the therapy contour

Date: 2026-08-30 · Status: approved · Commits: (1) voice, (2) therapy

## Stage A — Live 1:1 voice (ADR 0021)

- **A1. ADR-0021** — signaling over the existing dialogue WS; P2P media;
  the call state in-memory on the daphne process; ADR-0020 untouched.
- **A2. Backend signaling** (`apps/dialogue/calls.py` + `consumers.py`):
  - client → `call.ring` / `call.accept` / `call.decline` / `call.offer {sdp}` /
    `call.answer {sdp}` / `call.ice {candidate}` / `call.end`;
  - server → unicast over the participants' channels: `call.outgoing`, `call.incoming`,
    `call.accepted`, `call.offer`, `call.answer`, `call.ice`,
    `call.ended {reason}`; `call.busy` to the busy initiator;
  - one active call per dialogue and per actor; a ring timeout of 45s (server);
    a participant disconnect = `call.ended {reason:"connection"}`; a callee reconnect
    during ringing — a re-delivery of `call.incoming`;
    ICE flood control; SDP/candidate — size validators.
- **A3. ICE**: `GET /v1/rtc/config` (public) serves iceServers from
  `WEBRTC_TURN_URL/USERNAME/CREDENTIAL` (self-hosted coturn, DEPLOY.md 8.1);
  empty = only the browser's own candidates (LAN/perceptual NAT).
- **A4. Frontend** (`features/calls/`): a pure state machine `callMachine.ts`
  (vitest without WebRTC), `useCall.ts` (RTCPeerConnection, getUserMedia audio,
  mute, remote `<audio>`), `CallModal.tsx` + css; the embedding into DialoguePage
  (a button in the header, the call overlay); `useChatSocket` — a passthrough
  of `call.*` (an onCall callback + sendCall). Anti-Panic closes the WS → the call
  dies together with the signaling (deliberately).
- **A5. i18n** `calls.*` (ru/en), tests: vitest (the machine, the catalog), pytest
  (test_calls.py: ring/accept/relay/decline/busy/disconnect).

## Stage B — The therapy contour (ADR 0022), a seedling

- **B1. ADR-0022**: a therapist ≠ a Helper (ADR-0010 stays); the backend — only
  statuses and references; the payments — a direct client → therapist transfer (Solana Pay),
  the payment confirmation **manually by the therapist**; no keys/processing.
- **B2. Backend** `apps/therapy`: the models `TherapistProfile` (an invite token
  from the admin, a pseudonym, the approach, languages, the rate in SOL, a Solana address, active),
  `TherapySession` (client, therapist, the status `awaiting_payment →
  claimed → paid → active → done/declined`, the price); the API:
  `GET /therapy/profiles` (public, active only),
  `POST /therapy/sessions` (client), `GET /me/therapy/*` (both sides),
  `POST /therapy/sessions/{id}/claim|confirm|decline|complete` (therapist),
  the admin invite via the Django admin; tests.
- **B3. Frontend** `features/therapy/`: the "Therapy" page (catalog + request),
  the cabinets of both sides, the payment modal: a Solana Pay QR (a `solana:` deeplink
  + a link) by the fund pattern, the "I paid" button, the confirmation screen
  at the therapist. After `paid` — a 1:1 dialogue + the call button
  (stage A).
- **B4. i18n** `therapy.*` (the catalog cap 560 → 640 + a flatten.test sync),
  PRIVACY.md, ROADMAP, PROGRESS.
