#!/usr/bin/env bash
# GENERATED FILE — do not edit manually. Run: make types
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$REPO_ROOT/packages/shared-types/src/index.ts"
OPENAPI_JSON="$REPO_ROOT/packages/shared-types/openapi.json"

echo "📄 Generating TypeScript types from OpenAPI spec..."

# Prefer offline export (no running API); fall back to a live OpenAPI URL.
# Git Bash exposes the Windows interpreter as python.exe, while CI uses python.
PYTHON_CMD="${PYTHON:-}"
if [[ -z "$PYTHON_CMD" ]]; then
  for candidate in python python.exe python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_CMD="$candidate"
      break
    fi
  done
fi

EXPORT_SCRIPT="$REPO_ROOT/scripts/export_openapi.py"
if [[ "$PYTHON_CMD" == *.exe ]]; then
  if command -v wslpath >/dev/null 2>&1; then
    EXPORT_SCRIPT="$(wslpath -w "$EXPORT_SCRIPT")"
  elif command -v cygpath >/dev/null 2>&1; then
    EXPORT_SCRIPT="$(cygpath -w "$EXPORT_SCRIPT")"
  fi
fi

if [[ -n "$PYTHON_CMD" ]] && "$PYTHON_CMD" "$EXPORT_SCRIPT"; then
  echo "   OpenAPI schema exported (offline)."
else
  API_URL="${API_URL:-http://localhost:8000}"
  echo "   Offline export failed; fetching from $API_URL/openapi.json..."
  curl -sf "$API_URL/openapi.json" -o "$OPENAPI_JSON"
fi
test -s "$OPENAPI_JSON"

# Generate TypeScript types using the exact toolchain captured by package-lock.json.
echo "   Running openapi-typescript..."
cd "$REPO_ROOT/packages/shared-types"
npm ci --no-audit --no-fund
npm exec --no -- openapi-typescript openapi.json --output src/index.ts

echo "   ✅ OpenAPI and TypeScript contracts written to packages/shared-types"
