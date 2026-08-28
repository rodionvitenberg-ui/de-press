# Building de-press Desktop (tdesktop) on Linux

Upstream: [building-linux.md](https://github.com/telegramdesktop/tdesktop/blob/dev/docs/building-linux.md)

## Requirements

- **Docker** installed and working (`docker run hello-world`)
- **Git**, **poetry** (for prepare script)  
  If system Python blocks pip: `python3 -m venv /tmp/poetry-venv && /tmp/poetry-venv/bin/pip install poetry`
- Disk: prefer **≥40–60 GB free** (image + build trees)
- RAM: ideally **≥16 GB**; heavy linking may OOM on 8–14 GB under load
- Telegram **api_id** / **api_hash** from [my.telegram.org](https://my.telegram.org) / [obtaining_api_id](https://core.telegram.org/api/obtaining_api_id)

## Steps (summary)

```bash
cd native/desktop
./scripts/fetch_tdesktop.sh          # clone --recursive into ./tdesktop

# Prepare libraries (upstream script; builds docker image tdesktop:centos_env)
./tdesktop/Telegram/build/prepare/linux.sh

export TDESKTOP_API_ID=YOUR_ID
export TDESKTOP_API_HASH=YOUR_HASH
./scripts/build_linux_docker.sh      # wraps official docker run
```

Debug build:

```bash
export CONFIG=Debug
./scripts/build_linux_docker.sh
```

## Outputs

Built artifacts under `tdesktop/out/` (see upstream).

## de-press API (runtime, later)

Local backend while testing haven features:

```bash
# separate terminal
cd backend && source .venv/bin/activate
daphne -b 127.0.0.1 -p 8005 config.asgi:application
```

Desktop panel will call `http://127.0.0.1:8005/api/v1/...` (configurable).

## Troubleshooting

| Issue | Hint |
|-------|------|
| Docker permission | user in `docker` group or rootless docker |
| OOM during link | close browsers, add swap, Debug build first |
| Disk full | prune docker: `docker system prune -a` (careful) |
| Missing API keys | build fails configure without TDESKTOP_API_ID/HASH |
