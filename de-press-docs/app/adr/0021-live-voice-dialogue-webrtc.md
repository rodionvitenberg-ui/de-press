# ADR 0021: Live 1:1 voice in the dialogue — WebRTC with signaling over the dialogue WS

Date: 2026-08-30
Status: accepted

## Context

In the dialogue (Initiated Dialogue, 1:1) a live voice call is needed: sometimes
it is easier for the participants to talk than to type, and a live voice builds
more trust than anonymous text. The realtime infrastructure already exists: Django
Channels, WS `/ws/dialogues/<id>/` with `ActorAuthMiddleware` (the participant is
verified on connect), the client socket registry with Anti-Panic. WebRTC has not
been used in the product code. The privacy requirements: the media stream must not
settle on the server; the signaling must not reveal anything extra; registration
is not required.

## Decision

- **Signaling — over the existing dialogue WS.** New `call.*` events on the same
  connection (unicast by the participants' `channel_name`, the call state in
  `apps/dialogue/calls.py`). A separate WS route and a separate signaling schema
  are not needed: the participants are already verified.
- **Media — P2P (SRTP/DTLS) directly between the browsers.** The server does
  not participate in the stream, records nothing, stores nothing.
- **The call state — in-memory on the daphne process** (a single process per
  DEPLOY.md), no DB and no Redis. The call dies together with the signaling
  process — that is fine: the client socket registry breaks the call anyway on
  a WS loss (including Anti-Panic).
- **A two-phase handshake**: the initiator sends `call.ring`, the media SDP is
  not created until the other side accepts (`call.accept`) — the SDP is not
  sent to someone who did not agree to the call. Then `call.offer` /
  `call.answer` / trickle `call.ice`.
- **The limits**: one active call per dialogue and per actor (`call.busy`);
  a ring timeout of 45s on the server; a participant disconnect = the end of
  the call (`reason: "connection"`); a re-delivery of `call.incoming` on a
  callee reconnect during the ring.
- **ICE/TURN — self-hosted coturn** (`WEBRTC_TURN_URL/USERNAME/CREDENTIAL`,
  the public `GET /v1/rtc/config`). Static TURN credentials — a deliberate v1
  compromise: the server is ours, the firewall limits the relay ports; ephemeral
  credentials (the coturn REST API) — later. Without TURN the call works on
  LAN and behind perceptual NATs.
- **ADR-0020 is untouched**: the call is free for the participants, money is
  never mentioned.

## Consequences

- +`apps/dialogue/calls.py`, an extension of `DialogueConsumer`, `GET /v1/rtc/config`,
  a coturn section in DEPLOY.md; on the frontend — the seed of `features/calls/`
  (a state machine, `useCall`, `CallModal`) embedded into DialoguePage.
- The call is audio-only 1:1 and only inside an open dialogue; group rooms and
  video are out of scope (see ROADMAP "Not doing").
- Several daphne processes (horizontal scale) will require moving the call state
  to a shared store — deliberately deferred (YAGNI).
