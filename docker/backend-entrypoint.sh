#!/bin/sh
set -e

# Optional DB seeding (only when SEED_DB env var is true)
if [ "${SEED_DB:-false}" = "true" ]; then
  echo "[entrypoint] SEED_DB=true: running seed script"
  # Run the Python seed script (errors don't abort the container startup)
  if python /app/scripts/seed_postgres.py; then
    echo "[entrypoint] DB seeding completed"
  else
    echo "[entrypoint] DB seeding failed" >&2
  fi
fi

# Exec the container's main process
exec "$@"
