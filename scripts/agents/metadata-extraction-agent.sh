#!/bin/sh
# Run the MetadataExtractionAgent through the SYNINT wrapper CLI.
#
# Usage: metadata-extraction-agent.sh <target> [extra synint-wrapper args...]
# Env: SYNINT_PATH (default: synint), SYNINT_TIMEOUT (default: 300)
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <target> [extra synint-wrapper args...]" >&2
  exit 2
fi

TARGET="$1"
shift

exec python -m src.python.agents.synint_wrapper \
  --agent MetadataExtractionAgent \
  --synint-path "${SYNINT_PATH:-synint}" \
  --timeout "${SYNINT_TIMEOUT:-300}" \
  --target "$TARGET" \
  "$@"
