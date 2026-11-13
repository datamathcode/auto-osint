#!/bin/sh
# Ensure a research playbook exists. Idempotent: never overwrites an existing file.
set -eu

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
fi

PLAYBOOK="src/python/research_playbook.mdx"

if [ -f "$PLAYBOOK" ]; then
  echo "Playbook already present: $PLAYBOOK"
  exit 0
fi

echo "Creating default playbook at $PLAYBOOK"
"$PYTHON" - <<'PY'
from src.python import research_playbook

metadata = research_playbook.create_default_playbook()
research_playbook.save(metadata)
print(f"Wrote {research_playbook.RESEARCH_PLAYBOOK_PATH}")
PY
