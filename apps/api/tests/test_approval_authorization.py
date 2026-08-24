"""Approval decisions must enforce the current workflow step server-side."""

import pytest
from fastapi import HTTPException

from app.models.organization import (
    ApprovalDecision,
    ApprovalWorkflow,
    ContentApproval,
    Organization,
    Workspace,
    WorkspaceMember,
)
from app.models.user import User
from app.services import approval_service


def _authenticated_user(client, db, email: str) -> tuple[User, dict[str, str]]:
    password = "approval-test-password"
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": email.split("@")[0]},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    user = db.query(User).filter(User.email == email).one()
    return user, {"Authorization": f"Bearer {login.json()['access_token']}"}


def _workspace(db, suffix: str) -> Workspace:
    organization = Organization(
        id=f"approval-organization-{suffix}",
        name=f"Approval Organization {suffix}",
        slug=f"approval-organization-{suffix}",
    )
    workspace = Workspace(
        id=f"approval-workspace-{suffix}",
        organization=organization,
        name=f"Approval Workspace {suffix}",
        slug=f"approval-workspace-{suffix}",
    )
    db.add_all([organization, workspace])
    db.flush()
    return workspace


def _add_member(db, workspace: Workspace, user: User, role: str) -> None:
    db.add(
        WorkspaceMember(
            id=f"approval-member-{workspace.id}-{user.id}",
            workspace_id=workspace.id,
            user_id=user.id,
            role=role,
            permissions={},
        )
    )
    db.flush()


def _pending_approval(
    db,
    workspace: Workspace,
    requester: User,
    *,
    suffix: str,
    step: dict,
    content_id: str | None = None,
) -> ContentApproval:
    workflow = ApprovalWorkflow(
        id=f"approval-workflow-{suffix}",
        workspace_id=workspace.id,
        name=f"Workflow {suffix}",
        content_type="post",
        steps=[step],
        is_active=True,
    )
    approval = ContentApproval(
        id=f"content-approval-{suffix}",
        workspace_id=workspace.id,
        content_type="post",
        content_id=content_id or f"post-{suffix}",
        workflow_id=workflow.id,
        current_step=0,
        status="pending",
        requested_by=requester.id,
    )
    db.add_all([workflow, approval])
    db.commit()
    return approval


def test_ineligible_actor_cannot_decide_current_step(client, db) -> None:
    requester, _ = _authenticated_user(client, db, "approval-requester@example.com")
    actor, actor_headers = _authenticated_user(client, db, "approval-viewer@example.com")
    workspace = _workspace(db, "ineligible")
    _add_member(db, workspace, requester, "manager")
    _add_member(db, workspace, actor, "viewer")
    approval = _pending_approval(
        db,
        workspace,
        requester,
        suffix="ineligible",
        step={"step_number": 1, "role_required": "manager", "title": "Manager review"},
    )

    response = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**actor_headers, "X-Workspace-ID": workspace.id},
        json={
            "expected_step": 0,
            "decision": "approved",
            "comments": "I should not be able to approve",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == (
        "You are not eligible to approve the current workflow step"
    )
    db.expire_all()
    assert db.get(ContentApproval, approval.id).status == "pending"
    assert (
        db.query(ApprovalDecision)
        .filter(ApprovalDecision.approval_id == approval.id)
        .count()
        == 0
    )


def test_eligible_role_can_decide_current_step(client, db) -> None:
    actor, actor_headers = _authenticated_user(client, db, "approval-manager@example.com")
    workspace = _workspace(db, "eligible")
    _add_member(db, workspace, actor, "manager")
    approval = _pending_approval(
        db,
        workspace,
        actor,
        suffix="eligible",
        step={"step_number": 1, "role_required": "manager", "title": "Manager review"},
    )

    response = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**actor_headers, "X-Workspace-ID": workspace.id},
        json={"expected_step": 0, "decision": "approved"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert (
        db.query(ApprovalDecision)
        .filter(ApprovalDecision.approval_id == approval.id)
        .count()
        == 1
    )


def test_service_rejects_unknown_decision_value(db) -> None:
    requester = User(
        id="invalid-decision-user",
        email="invalid-decision@example.com",
        hashed_password="unused",
        name="Invalid Decision",
    )
    db.add(requester)
    workspace = _workspace(db, "invalid-decision")
    _add_member(db, workspace, requester, "manager")
    approval = _pending_approval(
        db,
        workspace,
        requester,
        suffix="invalid-decision",
        step={"step_number": 1, "role_required": "manager", "title": "Manager review"},
    )

    with pytest.raises(HTTPException) as exc_info:
        approval_service.make_decision(
            db=db,
            approval=approval,
            approver=requester,
            expected_step=0,
            decision="silently_approved",
        )

    assert exc_info.value.status_code == 400
    assert (
        db.query(ApprovalDecision)
        .filter(ApprovalDecision.approval_id == approval.id)
        .count()
        == 0
    )


def test_status_lookup_is_scoped_to_selected_workspace(client, db) -> None:
    user, headers = _authenticated_user(client, db, "approval-status@example.com")
    workspace_a = _workspace(db, "status-a")
    workspace_b = _workspace(db, "status-b")
    _add_member(db, workspace_a, user, "manager")
    _add_member(db, workspace_b, user, "manager")
    shared_content_id = "shared-content-id"
    approval_a = _pending_approval(
        db,
        workspace_a,
        user,
        suffix="status-a",
        content_id=shared_content_id,
        step={"step_number": 1, "role_required": "manager", "title": "A review"},
    )
    _pending_approval(
        db,
        workspace_b,
        user,
        suffix="status-b",
        content_id=shared_content_id,
        step={"step_number": 1, "role_required": "manager", "title": "B review"},
    )

    response = client.get(
        f"/api/v1/approvals/status/post/{shared_content_id}",
        headers={**headers, "X-Workspace-ID": workspace_a.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == approval_a.id
    assert response.json()["workspace_id"] == workspace_a.id


def test_specific_user_assignment_does_not_fall_through_to_role(client, db) -> None:
    assigned_user, _ = _authenticated_user(
        client, db, "approval-assigned-user@example.com"
    )
    actor, actor_headers = _authenticated_user(
        client, db, "approval-unassigned-manager@example.com"
    )
    workspace = _workspace(db, "specific-assignment")
    _add_member(db, workspace, assigned_user, "manager")
    _add_member(db, workspace, actor, "manager")
    approval = _pending_approval(
        db,
        workspace,
        assigned_user,
        suffix="specific-assignment",
        step={
            "step_number": 1,
            "user_id": assigned_user.id,
            "role_required": "manager",
            "title": "Assigned manager review",
        },
    )

    response = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**actor_headers, "X-Workspace-ID": workspace.id},
        json={"expected_step": 0, "decision": "approved"},
    )

    assert response.status_code == 403
    assert db.query(ApprovalDecision).filter_by(approval_id=approval.id).count() == 0


def test_explicit_approval_permission_denial_overrides_matching_role(client, db) -> None:
    from app.core.permissions import Permission

    actor, actor_headers = _authenticated_user(
        client, db, "approval-denied-manager@example.com"
    )
    workspace = _workspace(db, "approval-denied")
    db.add(
        WorkspaceMember(
            id=f"approval-member-{workspace.id}-{actor.id}",
            workspace_id=workspace.id,
            user_id=actor.id,
            role="manager",
            permissions={"denied": [Permission.AUTOMATION_APPROVE]},
        )
    )
    db.flush()
    approval = _pending_approval(
        db,
        workspace,
        actor,
        suffix="approval-denied",
        step={
            "step_number": 1,
            "role_required": "manager",
            "title": "Manager review",
        },
    )

    response = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**actor_headers, "X-Workspace-ID": workspace.id},
        json={"expected_step": 0, "decision": "approved"},
    )

    assert response.status_code == 403
    assert db.query(ApprovalDecision).filter_by(approval_id=approval.id).count() == 0


def test_stale_approval_transition_is_rejected(db) -> None:
    actor = User(
        id="stale-transition-user",
        email="stale-transition@example.com",
        hashed_password="unused",
        name="Stale Transition",
    )
    db.add(actor)
    workspace = _workspace(db, "stale-transition")
    _add_member(db, workspace, actor, "manager")
    approval = _pending_approval(
        db,
        workspace,
        actor,
        suffix="stale-transition",
        step={
            "step_number": 1,
            "role_required": "manager",
            "title": "First review",
        },
    )
    workflow = db.get(ApprovalWorkflow, approval.workflow_id)
    workflow.steps = [
        workflow.steps[0],
        {
            "step_number": 2,
            "role_required": "manager",
            "title": "Second review",
        },
    ]
    db.commit()

    stale_approval = ContentApproval(
        id=approval.id,
        workspace_id=approval.workspace_id,
        content_type=approval.content_type,
        content_id=approval.content_id,
        workflow_id=approval.workflow_id,
        current_step=0,
        status="pending",
        requested_by=approval.requested_by,
    )
    db.query(ContentApproval).filter(ContentApproval.id == approval.id).update(
        {ContentApproval.current_step: 1},
        synchronize_session=False,
    )
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        approval_service.make_decision(
            db=db,
            approval=stale_approval,
            approver=actor,
            expected_step=0,
            decision="approved",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Approval state changed; refresh and retry"
    assert db.query(ApprovalDecision).filter_by(approval_id=approval.id).count() == 0


def test_delayed_retry_cannot_approve_the_next_step(client, db) -> None:
    actor, headers = _authenticated_user(
        client, db, "approval-delayed-retry@example.com"
    )
    workspace = _workspace(db, "delayed-retry")
    _add_member(db, workspace, actor, "manager")
    approval = _pending_approval(
        db,
        workspace,
        actor,
        suffix="delayed-retry",
        step={
            "step_number": 1,
            "role_required": "manager",
            "title": "First review",
        },
    )
    workflow = db.get(ApprovalWorkflow, approval.workflow_id)
    workflow.steps = [
        workflow.steps[0],
        {
            "step_number": 2,
            "role_required": "manager",
            "title": "Second review",
        },
    ]
    db.commit()

    first = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**headers, "X-Workspace-ID": workspace.id},
        json={"expected_step": 0, "decision": "approved"},
    )
    delayed_retry = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        headers={**headers, "X-Workspace-ID": workspace.id},
        json={"expected_step": 0, "decision": "approved"},
    )

    assert first.status_code == 200
    assert first.json()["current_step"] == 1
    assert first.json()["status"] == "pending"
    assert delayed_retry.status_code == 409
    assert delayed_retry.json()["error"]["message"] == (
        "Approval state changed; refresh and retry"
    )
    db.expire_all()
    persisted = db.get(ContentApproval, approval.id)
    assert persisted.current_step == 1
    assert persisted.status == "pending"
    assert db.query(ApprovalDecision).filter_by(approval_id=approval.id).count() == 1
