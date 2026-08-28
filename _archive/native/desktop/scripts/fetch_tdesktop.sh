#!/usr/bin/env bash
# Clone Telegram Desktop (recursive). Large; not committed to de-press git.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/tdesktop"

if [[ -d "$DEST/.git" ]]; then
  echo "Already cloned: $DEST"
  git -C "$DEST" fetch --depth 1 origin dev 2>/dev/null || git -C "$DEST" fetch --depth 1 origin master 2>/dev/null || true
  exit 0
fi

echo "Cloning tdesktop (recursive, depth 1) → $DEST"
echo "This takes a while and needs network + disk."
git clone --depth 1 --recursive --shallow-submodules \
  https://github.com/telegramdesktop/tdesktop.git \
  "$DEST"

echo "Done. Next: read docs/BUILD.md and run Telegram/build/prepare/linux.sh"
