#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE="$DIR/index.html"

if [[ ! -f "$FILE" ]]; then
  echo "index.html not found"
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$FILE"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$FILE"
else
  echo "No opener found. Please open $FILE in a browser manually."
fi
