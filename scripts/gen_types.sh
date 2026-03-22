#!/usr/bin/env bash
# GENERATED FILE — do not edit manually. Run: make types
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$REPO_ROOT/packages/shared-types/src/index.ts"
OPENAPI_JSON="$REPO_ROOT/packages/shared-types/openapi.json"
API_URL="${API_URL:-http://localhost:8000}"

echo "📄 Generating TypeScript types from OpenAPI spec..."

# Fetch the OpenAPI schema from the running FastAPI server
echo "   Fetching OpenAPI schema from $API_URL/openapi.json..."
curl -sf "$API_URL/openapi.json" -o "$OPENAPI_JSON"

# Generate TypeScript types using openapi-typescript
echo "   Running openapi-typescript..."
cd "$REPO_ROOT/packages/shared-types"
npx openapi-typescript "$OPENAPI_JSON" --output src/index.ts

# Prepend the generated file header
HEADER="// GENERATED FILE — do not edit manually. Run: make types\n// Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)\n\n"
CONTENT=$(cat "$OUTPUT")
printf "%b%s" "$HEADER" "$CONTENT" > "$OUTPUT"

# Cleanup temp file
rm -f "$OPENAPI_JSON"

echo "   ✅ Types written to packages/shared-types/src/index.ts"
