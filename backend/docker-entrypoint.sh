#!/bin/sh
# Docker entrypoint: apply migrations, optionally seed demo data, then exec CMD.
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

if [ "${SEED:-0}" = "1" ]; then
  echo "SEED=1 — running manage.py seed_local ..."
  python manage.py seed_local
fi

exec "$@"
