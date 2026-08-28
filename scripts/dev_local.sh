#!/usr/bin/env bash
# Local stack: system Postgres `depress` + Redis + Daphne :8005 + browser Vite :5174.
# Browser app: apps/browser (independent of Mini App). No Docker required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source "$ROOT/.env"
  set +a
fi

POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-depress}"
POSTGRES_USER="${POSTGRES_USER:-depress}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-depress}"

echo "==> Checking Postgres ${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
if command -v pg_isready >/dev/null 2>&1; then
  pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" || {
    echo "Postgres is not accepting connections on ${POSTGRES_HOST}:${POSTGRES_PORT}"
    echo "Start system PostgreSQL (no docker compose needed for de-press)."
    exit 1
  }
fi

export PGPASSWORD="$POSTGRES_PASSWORD"
if command -v psql >/dev/null 2>&1; then
  if ! psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" >/dev/null 2>&1; then
    echo "Cannot connect as ${POSTGRES_USER} to database ${POSTGRES_DB}."
    echo "One-time setup:"
    echo "  sudo -u postgres psql -c \"CREATE ROLE depress WITH LOGIN PASSWORD 'depress';\""
    echo "  sudo -u postgres psql -c \"CREATE DATABASE depress OWNER depress;\""
    exit 1
  fi
fi

# Never accidental SQLite in this script
unset DEPRESS_USE_SQLITE || true

echo "==> Backend migrate + seed"
cd "$ROOT/backend"
# shellcheck disable=SC1091
source .venv/bin/activate
python manage.py migrate --noinput
python manage.py seed_local
python manage.py check_db

echo "==> Starting Daphne on 127.0.0.1:8005"
pkill -f "daphne -b 127.0.0.1 -p 8005" 2>/dev/null || true
nohup daphne -b 127.0.0.1 -p 8005 config.asgi:application \
  > /tmp/depress_daphne.log 2>&1 &
sleep 2
curl -sf "http://127.0.0.1:8005/api/v1/health" | head -c 200 || {
  echo "Daphne failed to start; see /tmp/depress_daphne.log"
  tail -20 /tmp/depress_daphne.log || true
  exit 1
}
echo

echo "==> Starting browser app (apps/browser) on 127.0.0.1:5174"
cd "$ROOT/apps/browser"
if [[ ! -d node_modules ]]; then
  npm install
fi
pkill -f "vite.*5174" 2>/dev/null || true
# Match common vite process lines
pkill -f "node.*vite" 2>/dev/null || true
nohup npm run dev > /tmp/depress_vite.log 2>&1 &
sleep 3
curl -sf -o /dev/null "http://127.0.0.1:5174/" || {
  echo "Vite not ready yet; see /tmp/depress_vite.log"
  tail -30 /tmp/depress_vite.log || true
}

echo
echo "Ready:"
echo "  Browser: http://127.0.0.1:5174/feed   (apps/browser)"
echo "  Mini:    cd apps/mini-app && npm run dev  (:5175, separate app)"
echo "  API:  http://127.0.0.1:8005/api/v1/stories"
echo "  Docs: http://127.0.0.1:8005/api/docs"
echo "  Demo: seed@de-press.local / seedseed12  (avatar → login)"
echo "  Logs: /tmp/depress_daphne.log  /tmp/depress_vite.log"
echo "  DB:   cd backend && source .venv/bin/activate && python manage.py check_db"
echo
echo "Note: legacy Next is under _archive/legacy/next-frontend/ — not started."
