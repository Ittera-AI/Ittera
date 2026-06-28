"""Public-route allowlist and per-router scope source of truth.

This module is the single, explicit source of truth for **which routes are
intentionally reachable without an authenticated identity** and, more broadly,
for the authorization scope of every mounted router.

It exists because the API enforces authentication per-route (via the
``get_current_user`` dependency) rather than through a global gate. A newly
added router that forgets the dependency would be silently public. To close that
gap, this module:

1. Enumerates the **documented public routes** (Requirement 2.1) so a test can
   assert that *every other* mounted route rejects unauthenticated requests
   (Property 3, "Every non-public route requires authentication").
2. Records the **per-router scope mapping** — public / user-scoped /
   admin-scoped — so the Audit Report (Requirement 2.4) can list, for each
   mounted router, the authorization control that applies to it and flag any
   route lacking an ownership or authorization control.

The documented public surface (Requirement 2.1) is:

* ``/health`` plus the liveness and readiness probes
* waitlist join and waitlist stats
* auth register / login / logout
* OAuth start + callback endpoints (auth Google/LinkedIn, social connect)

Everything not listed here is expected to require authentication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# API version prefix used by every business router mounted in ``main.py``.
API_PREFIX = "/api/v1"


class RouteScope(str, Enum):
    """Authorization scope a route is expected to enforce."""

    PUBLIC = "public"
    """Reachable without an authenticated identity."""

    USER_SCOPED = "user-scoped"
    """Requires an authenticated identity; data is scoped to that user."""

    ADMIN_SCOPED = "admin-scoped"
    """Requires an authenticated identity whose email is in ``ADMIN_EMAILS``."""


# ---------------------------------------------------------------------------
# Documented public routes (Requirement 2.1)
# ---------------------------------------------------------------------------
#
# Each entry is an (HTTP method, mounted path) pair. Paths are the fully
# mounted paths exactly as they appear on ``app.routes`` (including the router
# prefix), so the Property 3 test can compare them directly without recomputing
# prefixes. ``OAuth callbacks`` and their paired ``start`` endpoints are public
# because the social/auth OAuth flows resolve the user from a signed state or a
# single-use connect token, not from a bearer credential on the request.

#: Health, liveness, and readiness probes (Requirements 2.1, 11.2, 11.3).
HEALTH_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
    }
)

#: Waitlist join (POST) and waitlist stats (GET) — both anonymous (Requirement 2.1).
WAITLIST_PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", f"{API_PREFIX}/waitlist"),
        ("POST", f"{API_PREFIX}/waitlist"),
    }
)

#: Auth register / login / logout — credential-establishing routes (Requirement 2.1).
AUTH_PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("POST", f"{API_PREFIX}/auth/register"),
        ("POST", f"{API_PREFIX}/auth/login"),
        ("POST", f"{API_PREFIX}/auth/logout"),
    }
)

#: OAuth start + callback endpoints (Requirement 2.1). The user identity is
#: carried by a signed state / single-use connect token, never a session.
OAUTH_PUBLIC_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        # Auth-router OAuth (login/sign-in via Google & LinkedIn).
        ("GET", f"{API_PREFIX}/auth/google/start"),
        ("GET", f"{API_PREFIX}/auth/google/callback"),
        ("GET", f"{API_PREFIX}/auth/linkedin/start"),
        ("GET", f"{API_PREFIX}/auth/linkedin/callback"),
        # Social-connection OAuth (connect an existing account to a platform).
        ("GET", f"{API_PREFIX}/connect/twitter/start"),
        ("GET", f"{API_PREFIX}/connect/twitter/callback"),
        ("GET", f"{API_PREFIX}/connect/linkedin/start"),
        ("GET", f"{API_PREFIX}/connect/linkedin/callback"),
        ("GET", f"{API_PREFIX}/connect/instagram/start"),
        ("GET", f"{API_PREFIX}/connect/instagram/callback"),
    }
)

#: Framework-provided routes that are public by design (OpenAPI schema + docs UI).
#: These are not application endpoints but they appear on ``app.routes``, so the
#: Property 3 test must treat them as allowlisted rather than flag them.
FRAMEWORK_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }
)

#: The complete documented public allowlist as (method, path) pairs.
PUBLIC_ROUTES: frozenset[tuple[str, str]] = (
    HEALTH_ROUTES | WAITLIST_PUBLIC_ROUTES | AUTH_PUBLIC_ROUTES | OAUTH_PUBLIC_ROUTES
)

#: Convenience set of just the public paths (method-agnostic).
PUBLIC_PATHS: frozenset[str] = frozenset(path for _method, path in PUBLIC_ROUTES)


def is_public_route(path: str, method: str = "GET") -> bool:
    """Return ``True`` if ``(method, path)`` is an intentionally public route.

    Used by the Property 3 test to enumerate ``app.routes`` and assert that any
    route which is *not* public rejects unauthenticated requests. Both the
    documented application allowlist and the framework docs/schema routes are
    considered public.

    The match is exact against the mounted path template (e.g.
    ``/api/v1/auth/login`` or ``/api/v1/connect/{platform}/callback``). Method
    comparison is case-insensitive.
    """
    if path in FRAMEWORK_PUBLIC_PATHS:
        return True
    return (method.upper(), path) in PUBLIC_ROUTES


# ---------------------------------------------------------------------------
# Per-router scope mapping (Requirement 2.4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RouterScope:
    """Documents the authorization scope of a single mounted router.

    Attributes:
        name: The router module name (matches ``app/routers/<name>.py``).
        prefix: The mounted path prefix in ``main.py``.
        default_scope: The scope that applies to the router's routes unless an
            entry in ``route_overrides`` says otherwise.
        public_routes: ``(method, path)`` pairs on this router that are public.
        admin_routes: ``(method, path)`` pairs on this router gated by
            ``require_admin`` (email must be in ``ADMIN_EMAILS``).
        notes: Free-form audit notes (e.g. ownership-control mechanism).
    """

    name: str
    prefix: str
    default_scope: RouteScope
    public_routes: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    admin_routes: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    notes: str = ""


#: Authoritative per-router scope mapping consumed by the audit deliverable and
#: the Property 3 / Property 5 tests. Routers default to ``USER_SCOPED``; the
#: ``public_routes`` and ``admin_routes`` fields enumerate the exceptions.
ROUTER_SCOPES: tuple[RouterScope, ...] = (
    RouterScope(
        name="auth",
        prefix=f"{API_PREFIX}/auth",
        default_scope=RouteScope.USER_SCOPED,
        public_routes=AUTH_PUBLIC_ROUTES
        | frozenset(
            {
                ("GET", f"{API_PREFIX}/auth/google/start"),
                ("GET", f"{API_PREFIX}/auth/google/callback"),
                ("GET", f"{API_PREFIX}/auth/linkedin/start"),
                ("GET", f"{API_PREFIX}/auth/linkedin/callback"),
            }
        ),
        notes="register/login/logout + OAuth login flows are public; /me and "
        "/onboarding require get_current_user.",
    ),
    RouterScope(
        name="waitlist",
        prefix=f"{API_PREFIX}/waitlist",
        default_scope=RouteScope.USER_SCOPED,
        public_routes=WAITLIST_PUBLIC_ROUTES,
        admin_routes=frozenset(
            {
                ("GET", f"{API_PREFIX}/waitlist/admin/entries"),
                ("POST", f"{API_PREFIX}/waitlist/admin/approve"),
                ("POST", f"{API_PREFIX}/waitlist/admin/revoke"),
            }
        ),
        notes="join/stats are public; /me is user-scoped; /admin/* gated by "
        "require_admin against ADMIN_EMAILS.",
    ),
    RouterScope(
        name="social_oauth",
        prefix=f"{API_PREFIX}/connect",
        default_scope=RouteScope.USER_SCOPED,
        public_routes=frozenset(
            {
                ("GET", f"{API_PREFIX}/connect/twitter/start"),
                ("GET", f"{API_PREFIX}/connect/twitter/callback"),
                ("GET", f"{API_PREFIX}/connect/linkedin/start"),
                ("GET", f"{API_PREFIX}/connect/linkedin/callback"),
                ("GET", f"{API_PREFIX}/connect/instagram/start"),
                ("GET", f"{API_PREFIX}/connect/instagram/callback"),
            }
        ),
        notes="OAuth start/callback are public (state/connect-token bound); "
        "/status, /session, DELETE /{platform} require get_current_user.",
    ),
    RouterScope(
        name="onboarding",
        prefix=f"{API_PREFIX}/onboarding",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="context",
        prefix=f"{API_PREFIX}/context",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="linkedin",
        prefix=f"{API_PREFIX}/linkedin",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="brand_profile",
        prefix=f"{API_PREFIX}/brand-profile",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="trends",
        prefix=f"{API_PREFIX}/trends",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="content",
        prefix=f"{API_PREFIX}/content",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="analytics",
        prefix=f"{API_PREFIX}/analytics",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="users",
        prefix=f"{API_PREFIX}/users",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="calendar",
        prefix=f"{API_PREFIX}/calendar",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="repurpose",
        prefix=f"{API_PREFIX}/repurpose",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="coach",
        prefix=f"{API_PREFIX}/coach",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="radar",
        prefix=f"{API_PREFIX}/radar",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="social",
        prefix=f"{API_PREFIX}/social",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="sync",
        prefix=f"{API_PREFIX}/sync",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="persona",
        prefix=f"{API_PREFIX}/persona",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="storage",
        prefix=f"{API_PREFIX}/storage",
        default_scope=RouteScope.USER_SCOPED,
        notes="storage exposes its own /health and /status, both user-scoped "
        "(require get_current_user); not to be confused with the public /health.",
    ),
    RouterScope(
        name="organizations",
        prefix=f"{API_PREFIX}/organizations",
        default_scope=RouteScope.USER_SCOPED,
        notes="membership/role checks via permissions.py enforce per-resource "
        "authorization beyond authentication.",
    ),
    RouterScope(
        name="workspaces",
        prefix=f"{API_PREFIX}/workspaces",
        default_scope=RouteScope.USER_SCOPED,
        notes="resource access mediated by get_current_workspace + permissions.py.",
    ),
    RouterScope(
        name="predictions",
        prefix=f"{API_PREFIX}/predictions",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="competitors",
        prefix=f"{API_PREFIX}/competitors",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="reports",
        prefix=f"{API_PREFIX}/reports",
        default_scope=RouteScope.USER_SCOPED,
    ),
    RouterScope(
        name="approvals",
        prefix=f"{API_PREFIX}/approvals",
        default_scope=RouteScope.USER_SCOPED,
    ),
)


#: Index of router scopes by mounted prefix for quick lookup.
ROUTER_SCOPE_BY_PREFIX: dict[str, RouterScope] = {rs.prefix: rs for rs in ROUTER_SCOPES}


def scope_for_path(path: str, method: str = "GET") -> RouteScope:
    """Return the documented :class:`RouteScope` for a mounted ``(method, path)``.

    Resolution order:

    1. Explicit public allowlist (documented public routes + framework docs).
    2. Per-router ``admin_routes`` override (admin-scoped).
    3. Per-router ``public_routes`` override (public).
    4. The owning router's ``default_scope`` (matched by longest prefix).
    5. ``USER_SCOPED`` as the safe default for anything unmapped.
    """
    if is_public_route(path, method):
        return RouteScope.PUBLIC

    pair = (method.upper(), path)
    # Longest-prefix match so e.g. /api/v1/auth wins over a shorter prefix.
    for router in sorted(ROUTER_SCOPES, key=lambda r: len(r.prefix), reverse=True):
        if path == router.prefix or path.startswith(router.prefix + "/"):
            if pair in router.admin_routes:
                return RouteScope.ADMIN_SCOPED
            if pair in router.public_routes:
                return RouteScope.PUBLIC
            return router.default_scope

    return RouteScope.USER_SCOPED
