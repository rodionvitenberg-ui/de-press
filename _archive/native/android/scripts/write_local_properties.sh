#!/usr/bin/env bash
# Write Telegram/local.properties from env / native/desktop/.env
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TD="$ROOT/Telegram"
DESKTOP_ENV="$ROOT/../desktop/.env"
ANDROID_ENV="$ROOT/.env"

if [[ -f "$ANDROID_ENV" ]]; then
  set -a; # shellcheck disable=SC1090
  source "$ANDROID_ENV"; set +a
elif [[ -f "$DESKTOP_ENV" ]]; then
  set -a; # shellcheck disable=SC1090
  source "$DESKTOP_ENV"; set +a
fi

API_ID="${TDESKTOP_API_ID:-${APP_ID:-${TELEGRAM_API_ID:-}}}"
API_HASH="${TDESKTOP_API_HASH:-${APP_HASH:-${TELEGRAM_API_HASH:-}}}"
SDK_DIR="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Android/Sdk}}"

if [[ -z "$API_ID" || -z "$API_HASH" ]]; then
  echo "Need API id/hash in native/android/.env or native/desktop/.env" >&2
  exit 1
fi

if [[ ! -d "$TD" ]]; then
  echo "Clone first: ./scripts/fetch_telegram_android.sh" >&2
  exit 1
fi

OUT="$TD/local.properties"
{
  echo "sdk.dir=${SDK_DIR}"
  echo "APP_ID=${API_ID}"
  echo "APP_HASH=${API_HASH}"
} > "$OUT"
chmod 600 "$OUT"
echo "Wrote $OUT (sdk.dir + APP_ID/HASH). Verify names match upstream BuildVars expectations."
