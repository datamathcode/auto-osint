#!/bin/sh
# Initialise the database schema. Idempotent: safe to run repeatedly.
set -eu

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
fi

if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -a && . ./.env && set +a
fi

echo "Initialising database (${DATABASE_URL:-default SQLite})"
"$PYTHON" -m src.python.scripts.setup_database
echo "Done."
