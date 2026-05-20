"""Export FastAPI OpenAPI JSON without a running server (for `make types` / codegen)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "apps" / "api"


def main() -> None:
    sys.path.insert(0, str(API_ROOT))
    import main as api_main  # noqa: PLC0415 — must run after sys.path patch

    schema = api_main.app.openapi()
    out = REPO_ROOT / "packages" / "shared-types" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI schema to {out}")


if __name__ == "__main__":
    main()
