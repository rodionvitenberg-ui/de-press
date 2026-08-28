#!/usr/bin/env bash
# Shallow-clone official Telegram Web A (telegram-tt, GPLv3) into Mini App vendor.
# https://github.com/Ajaxy/telegram-tt
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/apps/mini-app/vendor/telegram-tt"
mkdir -p "$ROOT/apps/mini-app/vendor"
if [[ -d "$DEST/.git" ]]; then
  echo "Already present: $DEST"
  git -C "$DEST" pull --ff-only || true
  exit 0
fi
git clone --depth 1 --single-branch \
  https://github.com/Ajaxy/telegram-tt.git \
  "$DEST"
echo "Cloned Web A → $DEST"
echo "License: GPLv3 — see apps/mini-app/NOTICE.GPL.md"
