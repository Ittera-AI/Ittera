#!/usr/bin/env bash
# GENERATED FILE — do not edit manually. Run: make types
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$REPO_ROOT/packages/shared-types/src/index.ts"
OPENAPI_JSON="$REPO_ROOT/packages/shared-types/openapi.json"

echo "📄 Generating TypeScript types from OpenAPI spec..."

# Prefer offline export (no running API); fall back to a live OpenAPI URL.
if python "$REPO_ROOT/scripts/export_openapi.py"; then
  echo "   OpenAPI schema exported (offline)."
else
  API_URL="${API_URL:-http://localhost:8000}"
  echo "   Offline export failed; fetching from $API_URL/openapi.json..."
  curl -sf "$API_URL/openapi.json" -o "$OPENAPI_JSON"
fi
test -s "$OPENAPI_JSON"

# Generate TypeScript types using openapi-typescript
echo "   Running openapi-typescript..."
cd "$REPO_ROOT/packages/shared-types"
npm install --no-audit --no-fund
npx openapi-typescript "$OPENAPI_JSON" --output src/index.ts

# Optionally remove temp OpenAPI artifact (keep for debugging codegen issues)
rm -f "$OPENAPI_JSON"

echo "   ✅ Types written to packages/shared-types/src/index.ts"
