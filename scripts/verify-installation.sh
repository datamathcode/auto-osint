#!/bin/sh
# Check that the local installation can run auto-osint. Exit 1 on a hard failure.
set -eu

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
fi

failures=0
warnings=0

check() { # check <label> <command...>
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "ok    $label"
  else
    echo "FAIL  $label"
    failures=$((failures + 1))
  fi
}

optional() {
  label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "ok    $label"
  else
    echo "warn  $label (optional)"
    warnings=$((warnings + 1))
  fi
}

echo "Python"
check "python >= 3.10" "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
check "package importable" "$PYTHON" -c 'import src.python.main'
check "sqlalchemy" "$PYTHON" -c 'import sqlalchemy'
check "fastapi" "$PYTHON" -c 'import fastapi'
check "playbook file" "$PYTHON" -c 'from pathlib import Path; raise SystemExit(0 if Path("src/python/research_playbook.mdx").exists() else 1)'
check "database schema" "$PYTHON" -c '
from sqlalchemy import create_engine
from src.python.database import create_db_engine, init_db
engine = create_db_engine()
init_db(engine)
print("schema ok")
'

echo
echo "Frontend"
optional "node >= 18" node -e 'const [maj] = process.versions.node.split(".").map(Number); process.exit(maj >= 18 ? 0 : 1)'
optional "node_modules present" test -d node_modules

echo
echo "Optional OSINT tools"
optional "sherlock on PATH" sh -c 'command -v sherlock'
optional "holehe on PATH" sh -c 'command -v holehe'
optional "SYNINT on PATH" sh -c 'command -v "${SYNINT_PATH:-synint}"'

echo
echo "Configuration"
if [ -f .env ]; then
  echo "ok    .env present"
else
  echo "warn  .env missing (copy .env.example)"
  warnings=$((warnings + 1))
fi
if [ -n "${HIBP_API_KEY:-}" ]; then
  echo "ok    HIBP_API_KEY set"
else
  echo "warn  HIBP_API_KEY unset (breach lookups disabled)"
  warnings=$((warnings + 1))
fi

echo
if [ "$failures" -gt 0 ]; then
  echo "$failures required check(s) failed, $warnings warning(s)."
  exit 1
fi

echo "All required checks passed ($warnings warning(s))."
