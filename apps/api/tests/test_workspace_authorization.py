"""Fail-closed workspace resolution and effective-permission contracts."""

from app.core.permissions import (
    Permission,
    WORKSPACE_ROLE_PERMISSIONS,
    get_effective_workspace_permissions,
)
from app.models.organization import (
    Organization,
    OrganizationMember,
    Workspace,
    WorkspaceMember,
)
from app.models.user import User


def _authenticated_user(client, db, email: str) -> tuple[User, dict[str, str]]:
    password = "workspace-test-password"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": email.split("@")[0]},
    )
    assert response.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    user = db.query(User).filter(User.email == email).one()
    return user, {"Authorization": f"Bearer {login.json()['access_token']}"}


def _organization(db, suffix: str) -> Organization:
    organization = Organization(
        id=f"organization-{suffix}",
        name=f"Organization {suffix}",
        slug=f"organization-{suffix}",
    )
    db.add(organization)
    db.flush()
    return organization


def _workspace(db, organization: Organization, suffix: str) -> Workspace:
    workspace = Workspace(
        id=f"workspace-{suffix}",
        organization_id=organization.id,
        name=f"Workspace {suffix}",
        slug=f"workspace-{suffix}",
    )
    db.add(workspace)
    db.flush()
    return workspace


def _add_workspace_member(
    db,
    workspace: Workspace,
    user: User,
    *,
    role: str,
    permissions: dict | None = None,
) -> WorkspaceMember:
    member = WorkspaceMember(
        id=f"member-{workspace.id}-{user.id}",
        workspace_id=workspace.id,
        user_id=user.id,
        role=role,
        permissions=permissions or {},
    )
    db.add(member)
    db.commit()
    return member


def test_workspace_path_is_authoritative_without_header(client, db) -> None:
    user, headers = _authenticated_user(client, db, "path-member@example.com")
    organization = _organization(db, "path")
    workspace = _workspace(db, organization, "path")
    _add_workspace_member(db, workspace, user, role="manager")

    response = client.get(f"/api/v1/workspaces/{workspace.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == workspace.id


def test_conflicting_workspace_path_and_header_fail_closed(client, db) -> None:
    user, headers = _authenticated_user(client, db, "mismatch@example.com")
    organization = _organization(db, "mismatch")
    path_workspace = _workspace(db, organization, "path-target")
    header_workspace = _workspace(db, organization, "header-target")
    _add_workspace_member(db, header_workspace, user, role="manager")

    response = client.get(
        f"/api/v1/workspaces/{path_workspace.id}",
        headers={**headers, "X-Workspace-ID": header_workspace.id},
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == (
        "Workspace context does not match request path"
    )


def test_membership_in_another_workspace_does_not_authorize_path(client, db) -> None:
    user, headers = _authenticated_user(client, db, "other-workspace@example.com")
    organization = _organization(db, "other")
    requested_workspace = _workspace(db, organization, "requested")
    other_workspace = _workspace(db, organization, "other")
    _add_workspace_member(db, other_workspace, user, role="manager")

    response = client.get(
        f"/api/v1/workspaces/{requested_workspace.id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_organization_owner_can_access_workspace_without_direct_membership(client, db) -> None:
    user, headers = _authenticated_user(client, db, "org-owner@example.com")
    organization = _organization(db, "org-owner")
    workspace = _workspace(db, organization, "org-owner")
    db.add(
        OrganizationMember(
            id="organization-owner-membership",
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
            permissions={},
        )
    )
    db.commit()

    response = client.get(f"/api/v1/workspaces/{workspace.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == workspace.id
    assert response.json()["my_role"] == "owner"


def test_header_scoped_endpoint_requires_workspace_context(client, db) -> None:
    _, headers = _authenticated_user(client, db, "missing-context@example.com")

    response = client.get("/api/v1/competitors", headers=headers)

    assert response.status_code == 422


def test_explicit_workspace_view_denial_revokes_access(client, db) -> None:
    user, headers = _authenticated_user(client, db, "view-denied@example.com")
    organization = _organization(db, "view-denied")
    workspace = _workspace(db, organization, "view-denied")
    _add_workspace_member(
        db,
        workspace,
        user,
        role="manager",
        permissions={"denied": [Permission.WORKSPACE_VIEW]},
    )
    db.add(
        OrganizationMember(
            id="view-denied-organization-owner",
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
            permissions={},
        )
    )
    db.commit()

    response = client.get(f"/api/v1/workspaces/{workspace.id}", headers=headers)
    my_workspaces = client.get("/api/v1/workspaces/my", headers=headers)
    organization_workspaces = client.get(
        f"/api/v1/organizations/{organization.id}/workspaces",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Access denied to workspace"
    assert my_workspaces.status_code == 200
    assert all(item["id"] != workspace.id for item in my_workspaces.json())
    assert organization_workspaces.status_code == 200
    assert all(
        item["id"] != workspace.id for item in organization_workspaces.json()
    )


def test_explicit_allowed_permission_is_honored_by_dependency(client, db) -> None:
    user, headers = _authenticated_user(client, db, "allowed-override@example.com")
    organization = _organization(db, "allowed")
    workspace = _workspace(db, organization, "allowed")
    _add_workspace_member(
        db,
        workspace,
        user,
        role="viewer",
        permissions={"allowed": [Permission.AI_COMPETITOR_ANALYSIS]},
    )

    response = client.get(
        "/api/v1/competitors",
        headers={**headers, "X-Workspace-ID": workspace.id},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_explicit_denied_permission_overrides_role(client, db) -> None:
    user, headers = _authenticated_user(client, db, "denied-override@example.com")
    organization = _organization(db, "denied")
    workspace = _workspace(db, organization, "denied")
    _add_workspace_member(
        db,
        workspace,
        user,
        role="manager",
        permissions={"denied": [Permission.AI_COMPETITOR_ANALYSIS]},
    )

    response = client.get(
        "/api/v1/competitors",
        headers={**headers, "X-Workspace-ID": workspace.id},
    )

    assert response.status_code == 403


def test_member_permission_helpers_use_central_policy_and_deny_wins() -> None:
    organization_member = OrganizationMember(
        role="owner",
        permissions={
            "allowed": [Permission.REPORTS_WHITELABEL],
            "denied": [Permission.WORKSPACE_MANAGE],
        },
    )
    workspace_member = WorkspaceMember(
        role="manager",
        permissions={
            "allowed": [Permission.WORKSPACE_DELETE, Permission.CONTENT_PUBLISH],
            "denied": [Permission.CONTENT_PUBLISH],
        },
    )

    assert not organization_member.has_permission(Permission.WORKSPACE_MANAGE)
    assert Permission.WORKSPACE_MANAGE not in organization_member.get_permissions()
    assert workspace_member.has_permission(Permission.WORKSPACE_MANAGE)
    assert workspace_member.has_permission(Permission.WORKSPACE_DELETE)
    assert not workspace_member.has_permission(Permission.CONTENT_PUBLISH)
    assert Permission.CONTENT_PUBLISH not in workspace_member.get_permissions()


def test_workspace_role_matrix_uses_one_central_policy() -> None:
    expected_action_permissions = {
        "manager": {
            Permission.WORKSPACE_MANAGE,
            Permission.CONTENT_PUBLISH,
            Permission.AUTOMATION_APPROVE,
        },
        "editor": set(),
        "viewer": set(),
        "client": set(),
    }

    assert set(WORKSPACE_ROLE_PERMISSIONS) == set(expected_action_permissions)
    for role, expected in expected_action_permissions.items():
        effective = get_effective_workspace_permissions(role)
        assert Permission.WORKSPACE_VIEW in effective
        assert effective.intersection(
            {
                Permission.WORKSPACE_MANAGE,
                Permission.CONTENT_PUBLISH,
                Permission.AUTOMATION_APPROVE,
            }
        ) == expected

    assert get_effective_workspace_permissions("unknown-role") == set()


def test_authorization_context_real_stub_matches_versioned_contract(client, db) -> None:
    user, headers = _authenticated_user(
        client,
        db,
        "authorization-contract@example.com",
    )
    organization = _organization(db, "authorization-contract")
    workspace = _workspace(db, organization, "authorization-contract")
    _add_workspace_member(db, workspace, user, role="manager")

    response = client.get(
        f"/api/v1/workspaces/{workspace.id}/authorization-context",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "authorization-context.v1"
    assert payload["availability"] == "available"
    assert payload["workspace"] == {
        "schema_version": "workspace-summary.v1",
        "availability": "available",
        "reason": None,
        "id": workspace.id,
        "organization_id": organization.id,
        "organization_name": organization.name,
        "name": workspace.name,
        "slug": workspace.slug,
        "is_active": True,
    }
    assert payload["brand"]["schema_version"] == "brand-summary.v1"
    assert payload["brand"]["availability"] == "degraded"
    assert payload["brand"]["reason"] == "brand_profile_not_provisioned"
    assert payload["role"] == "manager"
    assert payload["permissions"] == sorted(payload["permissions"])
    assert payload["white_label"]["schema_version"] == "white-label-summary.v1"

    operation = client.app.openapi()["paths"][
        "/api/v1/workspaces/{workspace_id}/authorization-context"
    ]["get"]
    workspace_id_parameter = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "workspace_id"
    )
    assert workspace_id_parameter["in"] == "path"
    assert workspace_id_parameter["required"] is True
    assert workspace_id_parameter["schema"]["type"] == "string"

    response_schema = operation["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert response_schema == {"$ref": "#/components/schemas/AuthorizationContextV1"}
