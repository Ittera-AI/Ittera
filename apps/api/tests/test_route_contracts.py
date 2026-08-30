"""API route-composition and workspace-header contracts."""

from collections import Counter

from fastapi.routing import APIRoute

from main import app


_CANONICAL_BASES = {
    "/api/v1/organizations": "organizations",
    "/api/v1/workspaces": "workspaces",
    "/api/v1/approvals": "approvals",
    "/api/v1/competitors": "competitors",
    "/api/v1/predictions": "predictions",
    "/api/v1/reports": "reports",
}

_REPRESENTATIVE_OPERATIONS = {
    ("POST", "/api/v1/organizations"),
    ("GET", "/api/v1/workspaces/my"),
    ("GET", "/api/v1/approvals/workflows"),
    ("GET", "/api/v1/competitors"),
    ("POST", "/api/v1/predictions/performance"),
    ("GET", "/api/v1/reports/history"),
}


def _registered_operations() -> Counter[tuple[str, str]]:
    return Counter(
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in route.methods
    )


def test_all_canonical_router_operations_are_registered_once() -> None:
    operations = _registered_operations()
    assert {operation: count for operation, count in operations.items() if count != 1} == {}

    canonical_operations = {
        operation: count
        for operation, count in operations.items()
        if any(
            operation[1] == base or operation[1].startswith(f"{base}/")
            for base in _CANONICAL_BASES
        )
    }

    assert _REPRESENTATIVE_OPERATIONS <= canonical_operations.keys()
    assert canonical_operations
    assert {
        operation: count
        for operation, count in canonical_operations.items()
        if count != 1
    } == {}

    for base, segment in _CANONICAL_BASES.items():
        doubled_base = f"{base}/{segment}"
        assert not any(
            path == doubled_base or path.startswith(f"{doubled_base}/")
            for _, path in operations
        ), f"Accidental doubled router base remains registered: {doubled_base}"


def test_header_only_workspace_routes_require_workspace_header_in_openapi() -> None:
    schema = app.openapi()

    for path, method in (
        ("/api/v1/competitors", "get"),
        ("/api/v1/approvals/workflows", "get"),
        ("/api/v1/reports/white-label", "get"),
        ("/api/v1/reports/competitive", "post"),
        ("/api/v1/predictions/cache", "get"),
        ("/api/v1/predictions/cache/{prediction_id}", "delete"),
    ):
        parameters = schema["paths"][path][method]["parameters"]
        workspace_header = next(
            parameter
            for parameter in parameters
            if parameter.get("in") == "header"
            and parameter.get("name") == "X-Workspace-ID"
        )
        assert workspace_header["required"] is True
