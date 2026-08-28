# Pilot runbook — de-press.co

Closed cohort only. Not a medical product. Not production hard-shell.

**Product status:** core features through **v0.14** are in the repo (clouds, Hearers, Helper queue, voice notes).  
This runbook is about **running a closed pilot**, not finishing foundation.

## What testers get

- Quiet monologues + Silent Empathy (no likes)
- Quiet Phrases + private Support Clouds (free-text after Helper approve)
- Hearer List + Author Outreach (author-only)
- Author-only dialogue open + WebSocket chat + typing + optional voice notes
- Private **Inbox** (`/inbox`) reachable by magic-token from soft-notify email
- Soft-notify settings: opt-in + digest frequency (account and anonymous session)
- Report story/message, block peer
- Anti-Panic (kills WebSockets)
- Local mood patterns (IndexedDB only)
- UI language switcher (ru/en) on core screens

## Next vector being built (not in pilot yet)

- Frontend as the foundation: polished, warm UI/UX across all screens
- Circles (short video messages) — deleted when the dialogue closes
- Voice notes with configurable lifetime (delete on dialogue close / keep)
- Native Dynamic Multilingual: STT → translate → TTS so a Japanese user can talk to a Kyrgyz one, the Kyrgyz to a French one, etc.
- AI companion is the very last priority (already offline-safe in the repo)

## What we do **not** promise

- Therapy, crisis hotline replacement, diagnoses
- Perfect uptime, encryption of everything, mobile apps
- That silence means neglect — Pulse is private for authors

## One machine start (dev pilot)

Use **the same host** for API and cookies: `127.0.0.1` (not mix with `localhost`).

```bash
# 0) env
cp .env.example .env
# optional: AI_API_KEY=...

# 1) Postgres (системный; docker не нужен)
# Роль и БД создаются один раз:
#   sudo -u postgres psql -c "CREATE ROLE depress WITH LOGIN PASSWORD 'depress';"
#   sudo -u postgres psql -c "CREATE DATABASE depress OWNER depress;"

# 2) Backend (ASGI = HTTP + WebSocket)
cd backend
source .venv/bin/activate
pip install -r requirements/local.txt
python manage.py migrate
python manage.py seed_local   # stories + quiet phrases + demo dialogue
# or: seed_stories / seed_quiet_phrases / seed_dialogues
python manage.py check_db     # must show NAME=depress (not sqlite)
python manage.py createsuperuser   # once
daphne -b 127.0.0.1 -p 8005 config.asgi:application

# 3) Frontend (other terminal)
cd frontend
npm install
# .env.local:
#   NEXT_PUBLIC_API_URL=http://127.0.0.1:8005
#   NEXT_PUBLIC_WS_URL=ws://127.0.0.1:8005
#   BACKEND_UPSTREAM=http://127.0.0.1:8005
npm run dev -- -p 3005
```

- App: http://127.0.0.1:3005 (or localhost if you must — then keep API on matching host)
- Admin: http://127.0.0.1:8005/admin/
- API docs: http://127.0.0.1:8005/api/docs
- Health: http://127.0.0.1:8005/api/v1/health → `database`, `redis`, `channels`

## Operator checklist (daily)

1. Admin → **Reports** (status=open) → hide story or dismiss  
2. Spot-check **Stories** for spam  
3. If AI key set: try `/companion` crisis phrase → must redirect to 112/103 copy  
4. If Redis down: WS may degrade; HTTP chat fallback still works on client  

## Smoke checklist

```
[ ] GET /api/v1/health → status ok
[ ] register + login
[ ] publish story + topic filter
[ ] empathy twice → second "already"
[ ] report story → admin queue
[ ] dialogue request → accept → live channel + typing
[ ] reconnect: stop daphne briefly → client reconnects or HTTP fallback
[ ] anti-panic → WS closed
[ ] block peer in dialogue
[ ] report a message
[ ] AI offline or live
[ ] /patterns wipe local
```

Script: `scripts/smoke_api.sh` (HTTP only).

## Ethical metrics (manual, no public vanity)

- Stories with ≥1 empathy in 48h  
- Authors who open ≥1 dialogue when requests exist  
- Report resolution time  
- Anti-Panic uses  
- WS vs HTTP fallback rate (anecdotal)

## Incident notes

- **Cookie / auth weirdness:** ensure frontend and API share host (`127.0.0.1`).  
- **WS 4401/4403:** not a participant or no identity cookie.  
- **Crisis:** never “coach through” self-harm; product short-circuits AI.

## After pilot

Collect qualitative feedback → iterate safety/chat, then deploy compose for staging.

## Translation server (pilot ops)

Dynamic message translation uses a **dedicated** OpenAI-compatible server
(`TRANSLATOR_BASE_URL`), not the companion `AI_BASE_URL`. Django already
falls back to the AI gateway / offline marker if this process is down.

**Default host: CPU (llama.cpp).** This matches the weak pilot box.
vLLM is optional and only useful if a GPU is present.

**Model: Hy-MT1.5-1.8B.** CPU artifact: AngelSlim 1.25-bit GGUF (~440 MB).
2-bit GGUF (~574 MB) is the quality alternative on the same binary.

TTS is not in this pilot. STT stays cloud: set `STT_BASE_URL` / `STT_API_KEY`
(xAI or OpenAI); `OpenAICompatibleSTT` already speaks `/audio/transcriptions`.

### A. CPU — llama.cpp (default)

STQ 1.25-bit kernels are in llama.cpp PR 22836 (AngelSlim). Until it lands:

```bash
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
git fetch origin pull/22836/head:pr-22836-stq
git checkout pr-22836-stq
cmake -B build
cmake --build build --config Release -j
```

Weights (pick one):

```bash
pip install huggingface_hub
# 1.25-bit (~440 MB) — preferred on a weak CPU
huggingface-cli download AngelSlim/Hy-MT1.5-1.8B-1.25bit-GGUF \
  --local-dir /var/lib/depress/models/hy-mt-1.25
# or 2-bit (~574 MB)
# huggingface-cli download AngelSlim/Hy-MT1.5-1.8B-2bit-GGUF \
#   --local-dir /var/lib/depress/models/hy-mt-2
```

If the Hub repo ships a ready `.gguf`, pass that file to `llama-server`.
If it ships HF shards, convert + quantize as in AngelSlim Hy-MT docs
(`convert_hf_to_gguf.py` then `llama-quantize … STQ1_0`).

Serve (OpenAI-compatible `/v1/chat/completions`):

```bash
./build/bin/llama-server \
  --model /var/lib/depress/models/hy-mt-1.25/*.gguf \
  --alias Hy-MT1.5-1.8B \
  --host 127.0.0.1 \
  --port 8088 \
  --ctx-size 4096 \
  -ngl 0 \
  --jinja
```

Django `.env` on the same machine:

```
TRANSLATOR_BASE_URL=http://127.0.0.1:8088/v1
TRANSLATOR_MODEL=Hy-MT1.5-1.8B
TRANSLATOR_API_KEY=
```

The URL **must include `/v1`**. Empty `TRANSLATOR_API_KEY` is fine; Django
sends `not-needed` because the OpenAI SDK wants a non-empty string.

Smoke:

```bash
curl -s http://127.0.0.1:8088/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Hy-MT1.5-1.8B","temperature":0,"messages":[{"role":"user","content":"Translate to language code '"'"'en'"'"':\n\nМне тяжело это писать."}]}'
```

Then send a chat message from a `ru` user to an `en` UI (or POST
`/api/v1/messages/<id>/translate`). First token on CPU may take several
seconds; Django timeout is 30s then gateway fallback.

systemd is operator-local (out of repo). Bind to `127.0.0.1` only.

### B. GPU — vLLM (optional)

Only if a GPU exists. Do **not** feed 1.25-bit/2-bit GGUF to vLLM.

```bash
vllm serve tencent/HY-MT1.5-1.8B --port 8088 --host 127.0.0.1
```

Same Django env: `TRANSLATOR_BASE_URL=http://127.0.0.1:8088/v1`,
`TRANSLATOR_MODEL=tencent/HY-MT1.5-1.8B` (or whatever `vllm serve` prints).

### Out of scope here

- TTS (long-term).
- Shipping weights in git.
- Changing STT code — point `STT_BASE_URL` / `STT_API_KEY` at xAI when ready.
