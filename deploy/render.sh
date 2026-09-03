#!/usr/bin/env bash
# Render the deploy/*.template files into concrete artifacts in deploy/.
#
# Usage:
#   ./deploy/render.sh [path-to-env-file]
#
# The env file is optional; without one, values come from the environment
# and defaults. Only DEPRESS_DOMAIN and DEPRESS_APP_ROOT are required.
# Render variables may live in the same env file as the runtime values
# (e.g. /etc/depress/depress.env) — the app ignores unknown keys.
set -euo pipefail

ENV_FILE="${1:-/etc/depress/depress.env}"
if [[ -f "$ENV_FILE" ]]; then
  echo "Using env file: $ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

DEPRESS_APP_ROOT="${DEPRESS_APP_ROOT:-/opt/de-press}"
DEPRESS_USER="${DEPRESS_USER:-depress}"
DEPRESS_GROUP="${DEPRESS_GROUP:-depress}"
DEPRESS_ENV_FILE="${DEPRESS_ENV_FILE:-/etc/depress/depress.env}"
DEPRESS_API_PORT="${DEPRESS_API_PORT:-8000}"
DEPRESS_DB_NAME="${DEPRESS_DB_NAME:-depress}"
DEPRESS_BACKUP_DIR="${DEPRESS_BACKUP_DIR:-/var/backups/depress}"
ACME_WEBROOT="${ACME_WEBROOT:-/var/www/certbot}"
: "${DEPRESS_DOMAIN:?DEPRESS_DOMAIN is required (e.g. app.example.com)}"

export DEPRESS_DOMAIN DEPRESS_APP_ROOT DEPRESS_USER DEPRESS_GROUP \
  DEPRESS_ENV_FILE DEPRESS_API_PORT DEPRESS_DB_NAME DEPRESS_BACKUP_DIR ACME_WEBROOT

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBST='$DEPRESS_DOMAIN $DEPRESS_APP_ROOT $DEPRESS_USER $DEPRESS_GROUP $DEPRESS_ENV_FILE $DEPRESS_API_PORT $DEPRESS_DB_NAME $DEPRESS_BACKUP_DIR $ACME_WEBROOT'

for src in "$DIR"/*.template; do
  name="$(basename "$src" .template)"
  envsubst "$SUBST" < "$src" > "$DIR/$name"
  echo "Rendered $name"
done

echo "Done. Copy the rendered files to /etc/systemd/system/ and /etc/nginx/, then:"
echo "  sudo systemctl daemon-reload"
echo "  sudo nginx -t && sudo systemctl reload nginx"
