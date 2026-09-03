#!/usr/bin/env bash
# Fetch Telegram Web A (telegram-tt, GPLv3) into the Mini App vendor directory.
# https://github.com/Ajaxy/telegram-tt
#
# The revision is PINNED: a Mini App build must map to one known upstream source
# tree so the GPLv3 "Corresponding Source" obligation is reproducible
# (see apps/mini-app/NOTICE.GPL.md). vendor/ is gitignored — never committed.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/apps/mini-app/vendor/telegram-tt"
UPSTREAM="https://github.com/Ajaxy/telegram-tt.git"
# Pin: upstream master commit verified on 2026-08-28 ([Build]).
PIN="9cb10b20797dc09e33fcffee0ba390bb429c66d3"

if [[ -d "$DEST/.git" ]]; then
  current="$(git -C "$DEST" rev-parse HEAD)"
  if [[ "$current" == "$PIN" ]]; then
    echo "Already present and pinned: $DEST @ ${PIN:0:12}"
    exit 0
  fi
  echo "Re-pinning $DEST from ${current:0:12} to ${PIN:0:12}"
  git -C "$DEST" fetch --depth 1 origin "$PIN"
  git -C "$DEST" checkout --detach FETCH_HEAD
  echo "Pinned Telegram Web A @ ${PIN:0:12} → $DEST"
  echo "License: GPLv3 — see apps/mini-app/NOTICE.GPL.md"
  exit 0
fi

mkdir -p "$ROOT/apps/mini-app/vendor"
git clone --filter=blob:none --no-checkout "$UPSTREAM" "$DEST"
git -C "$DEST" fetch --depth 1 origin "$PIN"
git -C "$DEST" checkout --detach FETCH_HEAD
echo "Checked out Telegram Web A @ ${PIN:0:12} → $DEST"
echo "License: GPLv3 — see apps/mini-app/NOTICE.GPL.md"

