#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "[entrypoint] applying migrations"
  alembic upgrade head
fi

if [ "${RUN_SEEDS:-false}" = "true" ]; then
  echo "[entrypoint] running seeders"
  seed
fi

exec "$@"
