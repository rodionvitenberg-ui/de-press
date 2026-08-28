#!/usr/bin/env bash
# Official-style Docker build of tdesktop (requires prepare/linux.sh already run).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TD="$ROOT/tdesktop"

# Load keys from native/desktop/.env if present (gitignored)
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

if [[ ! -d "$TD/Telegram" ]]; then
  echo "Missing $TD — run ./scripts/fetch_tdesktop.sh first" >&2
  exit 1
fi

if [[ -z "${TDESKTOP_API_ID:-}" || -z "${TDESKTOP_API_HASH:-}" ]]; then
  echo "Set TDESKTOP_API_ID and TDESKTOP_API_HASH in native/desktop/.env" >&2
  exit 1
fi

if ! docker image inspect tdesktop:centos_env >/dev/null 2>&1; then
  echo "Docker image tdesktop:centos_env not found."
  echo "Run once:  PATH with poetry → $TD/Telegram/build/prepare/linux.sh" >&2
  exit 1
fi

cd "$TD"
CONFIG="${CONFIG:-}"
EXTRA_ENV=()
if [[ -n "$CONFIG" ]]; then
  EXTRA_ENV+=(-e "CONFIG=$CONFIG")
fi

echo "Building tdesktop via docker (api_id loaded)…"
# No -it: works under agents/CI (TTY optional)
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$PWD:/usr/src/tdesktop" \
  "${EXTRA_ENV[@]}" \
  tdesktop:centos_env \
  /usr/src/tdesktop/Telegram/build/docker/centos_env/build.sh \
  -D "TDESKTOP_API_ID=$TDESKTOP_API_ID" \
  -D "TDESKTOP_API_HASH=$TDESKTOP_API_HASH"

echo "Build finished. Check $TD/out/"
