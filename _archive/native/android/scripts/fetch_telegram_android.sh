#!/usr/bin/env bash
# Clone official Telegram Android sources (large; gitignored).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/Telegram"

if [[ -d "$DEST/.git" ]]; then
  echo "Already cloned: $DEST"
  exit 0
fi

echo "Cloning DrKLO/Telegram (depth 1) → $DEST"
git clone --depth 1 https://github.com/DrKLO/Telegram.git "$DEST"
echo "Done. See docs/BUILD.md for Android Studio / Gradle."
