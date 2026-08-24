"""Approval Workflow Service - multi-step content approval system.

Manages approval workflows for content publishing:
- Define workflow templates (e.g., Manager → Director → Legal)
- Request approvals for specific content
- Track approval decisions and status
- Send notifications for pending approvals
- Enforce approval before publishing

Features:
- Multi-step sequential approvals
- Role-based approver assignment
- Notifications (email, in-app)
- Approval history and audit trail
- Deadline tracking and reminders
"""

import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.models.organization import (
    ApprovalWorkflow,
    ContentApproval,
    ApprovalDecision,
    Workspace,
)
from app.models.user import User

logger = logging.getLogger(__name__)


def create_workflow(
    db: Session,
    workspace: Workspace,
    name: str,
    content_type: str,
    steps: list[dict],
) -> ApprovalWorkflow:
    """
    Create a new approval workflow for a workspace.
    
    Args:
        db: Database session
        workspace: Target workspace
        name: Workflow name (e.g., "Standard Review")
        content_type: Type of content (post, content_plan, etc.)
        steps: List of approval steps
            [
                {
                    "step_number": 1,
                    "role_required": "manager",  # or specific user_id
                    "title": "Manager Review",
                    "description": "Review for brand consistency",
                    "can_edit": True,  # Can approver edit content?
                    "auto_approve_hours": 48,  # Auto-approve after this many hours
                },
                ...
            ]
    
    Returns:
        Created workflow
    """
    workflow = ApprovalWorkflow(
        workspace_id=workspace.id,
        name=name,
        content_type=content_type,
        steps=steps,
        is_active=True,
    )
    
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    return workflow


def get_active_workflow(
    db: Session,
    workspace_id: str,
    content_type: str,
) -> ApprovalWorkflow | None:
    """Get the active workflow for a content type in a workspace."""
    return (
        db.query(ApprovalWorkflow)
        .filter(
            ApprovalWorkflow.workspace_id == workspace_id,
            ApprovalWorkflow.content_type == content_type,
            ApprovalWorkflow.is_active.is_(True),
        )
        .first()
    )


def request_approval(
    db: Session,
    workspace: Workspace,
    content_type: str,
    content_id: str,
    workflow_id: str | None,
    requested_by: User,
    note: str | None = None,
) -> ContentApproval:
    """
    Request approval for content.
    
    Args:
        db: Database session
        workspace: Workspace context
        content_type: Type of content (post, content_plan)
        content_id: Content ID
        workflow_id: Specific workflow to use (or None for default)
        requested_by: User requesting approval
        note: Optional note to approvers
    
    Returns:
        ContentApproval tracking object
    """
    # Get workflow
    workflow = None
    if workflow_id:
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == workflow_id,
            ApprovalWorkflow.workspace_id == workspace.id,
        ).first()
    
    if not workflow:
        workflow = get_active_workflow(db, workspace.id, content_type)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active approval workflow found for this content type",
        )
    
    # Create approval tracking
    approval = ContentApproval(
        workspace_id=workspace.id,
        content_type=content_type,
        content_id=content_id,
        workflow_id=workflow.id,
        current_step=0,
        status="pending",
        requested_by=requested_by.id,
    )
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # Notify first approver
    _notify_approvers(db, approval, workflow, note)
    
    return approval


def make_decision(
    db: Session,
    approval: ContentApproval,
    approver: User,
    expected_step: int,
    decision: str,  # approved, rejected, requested_changes
    comments: str | None = None,
) -> ContentApproval:
    """Record one approval decision against a client-observed step.

    The row is locked before the transition is validated. ``expected_step``
    binds the request to the workflow step the client actually reviewed, so a
    queued or delayed retry cannot approve a later step.
    """
    valid_decisions = {"approved", "rejected", "requested_changes"}
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid approval decision",
        )

    locked_approval = (
        db.query(ContentApproval)
        .filter(
            ContentApproval.id == approval.id,
            ContentApproval.workspace_id == approval.workspace_id,
        )
        .populate_existing()
        .with_for_update()
        .first()
    )
    if locked_approval is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found",
        )

    if (
        locked_approval.status != "pending"
        or locked_approval.current_step != expected_step
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval state changed; refresh and retry",
        )
    approval = locked_approval
    
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == approval.workflow_id,
        ApprovalWorkflow.workspace_id == approval.workspace_id,
    ).first()

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )

    steps = workflow.steps or []
    if not isinstance(steps, list) or not (
        0 <= approval.current_step < len(steps)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval workflow has no valid current step",
        )

    current_step = steps[approval.current_step]
    if not isinstance(current_step, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approval workflow has an invalid current step",
        )

    if not _user_can_approve_step(
        db,
        approver,
        approval.workspace_id,
        current_step,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not eligible to approve the current workflow step",
        )

    # Record decision only after the current step and actor have been validated.
    approval_decision = ApprovalDecision(
        approval_id=approval.id,
        step_number=approval.current_step,
        approver_id=approver.id,
        decision=decision,
        comments=comments,
    )
    db.add(approval_decision)
    
    # Update approval status
    if decision == "rejected":
        approval.status = "rejected"
        approval.completed_at = datetime.utcnow()
        
        # Notify requester
        _notify_requester(db, approval, "rejected", comments)
        
    elif decision == "requested_changes":
        # Send back to requester for changes
        approval.status = "changes_requested"
        
        # Notify requester
        _notify_requester(db, approval, "changes_requested", comments)
        
    else:  # approved
        # Check if there are more steps
        steps = workflow.steps or []
        if approval.current_step + 1 < len(steps):
            # Move to next step
            approval.current_step += 1
            db.flush()
            
            # Notify next approver
            _notify_approvers(db, approval, workflow)
        else:
            # All steps complete
            approval.status = "approved"
            approval.completed_at = datetime.utcnow()
            
            # Notify requester
            _notify_requester(db, approval, "approved")
    
    db.commit()
    db.refresh(approval)
    
    return approval


def resubmit_after_changes(
    db: Session,
    approval: ContentApproval,
    requester: User,
    change_notes: str | None = None,
) -> ContentApproval:
    """
    Resubmit content after changes were requested.
    
    Args:
        db: Database session
        approval: ContentApproval that was returned for changes
        requester: User resubmitting
        change_notes: Notes about what was changed
    
    Returns:
        Updated ContentApproval
    """
    if approval.status != "changes_requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not in changes_requested status",
        )
    
    # Reset to pending and keep current step
    approval.status = "pending"
    
    # Record resubmission
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == approval.workflow_id
    ).first()
    
    # Re-notify current approver
    _notify_approvers(db, approval, workflow, change_notes)
    
    db.commit()
    db.refresh(approval)
    
    return approval


def get_approval_status(
    db: Session,
    workspace_id: str,
    content_type: str,
    content_id: str,
) -> ContentApproval | None:
    """Get the latest approval status for content in one workspace."""
    return (
        db.query(ContentApproval)
        .filter(
            ContentApproval.workspace_id == workspace_id,
            ContentApproval.content_type == content_type,
            ContentApproval.content_id == content_id,
        )
        .order_by(ContentApproval.requested_at.desc())
        .first()
    )


def get_pending_approvals_for_user(
    db: Session,
    user: User,
    workspace_ids: list[str] | None = None,
) -> list[ContentApproval]:
    """
    Get all pending approvals awaiting this user's decision.
    
    Checks user's role in each workspace against workflow step requirements.
    """
    # Base query for pending approvals
    query = (
        db.query(ContentApproval)
        .filter(ContentApproval.status == "pending")
    )
    
    if workspace_ids:
        query = query.filter(ContentApproval.workspace_id.in_(workspace_ids))
    
    pending = query.all()
    
    # Filter to those where user is the current approver
    user_approvals = []
    for approval in pending:
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == approval.workflow_id
        ).first()
        
        if not workflow or not workflow.steps:
            continue
        
        steps = workflow.steps
        if approval.current_step >= len(steps):
            continue
        
        current_step = steps[approval.current_step]
        
        # Check if user matches this step
        if _user_can_approve_step(db, user, approval.workspace_id, current_step):
            user_approvals.append(approval)
    
    return user_approvals


def _user_can_approve_step(
    db: Session,
    user: User,
    workspace_id: str,
    step: dict,
) -> bool:
    """Check assignment and effective approval permission for one step."""
    if not isinstance(step, dict):
        return False

    from app.models.organization import OrganizationMember, WorkspaceMember

    ws_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    org_member = None
    if workspace is not None:
        org_member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == workspace.organization_id,
                OrganizationMember.user_id == user.id,
            )
            .first()
        )

    # A direct workspace membership is authoritative for effective permissions;
    # organization permissions are the fallback only when no direct membership
    # exists. Explicit denies therefore remain vetoes in approval enforcement.
    if ws_member is not None:
        permissions = ws_member.get_permissions()
    elif org_member is not None:
        permissions = org_member.get_permissions()
    else:
        return False

    if Permission.AUTOMATION_APPROVE not in permissions:
        return False

    # A specific user assignment is exclusive. It must never fall through to a
    # role match for a different actor when both legacy fields are populated.
    assigned_user_id = step.get("user_id")
    if assigned_user_id is not None:
        return isinstance(assigned_user_id, str) and assigned_user_id == user.id

    role_required = step.get("role_required")
    if not isinstance(role_required, str) or not role_required:
        return False

    if ws_member is not None and ws_member.role == role_required:
        return True

    return (
        role_required in {"owner", "admin"}
        and org_member is not None
        and org_member.role == role_required
    )


def _notify_approvers(
    db: Session,
    approval: ContentApproval,
    workflow: ApprovalWorkflow,
    note: str | None = None,
) -> None:
    """Notify approvers for current step."""
    steps = workflow.steps or []
    if approval.current_step >= len(steps):
        return
    
    current_step = steps[approval.current_step]
    
    # Find approvers for this step
    approvers = _get_step_approvers(db, approval.workspace_id, current_step)
    
    # TODO: Send email notification
    # TODO: Send in-app notification
    
    for approver in approvers:
        logger.info(
            f"Approval notification: Content {approval.content_id} "
            f"awaiting approval from {approver.email} (step {approval.current_step})"
        )


def _get_step_approvers(
    db: Session,
    workspace_id: str,
    step: dict,
) -> list[User]:
    """Get users who can approve a workflow step."""
    # Specific user assignment
    if step.get("user_id"):
        user = db.query(User).filter(User.id == step["user_id"]).first()
        return [user] if user else []
    
    # Role-based assignment
    role_required = step.get("role_required")
    if not role_required:
        return []
    
    from app.models.organization import WorkspaceMember, OrganizationMember
    
    # Get workspace members with role
    ws_members = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == role_required,
        )
        .all()
    )
    
    users = []
    for member in ws_members:
        user = db.query(User).filter(User.id == member.user_id).first()
        if user:
            users.append(user)
    
    # Also check org-level roles for owner/admin
    if role_required in ("owner", "admin") and not users:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if workspace:
            org_members = (
                db.query(OrganizationMember)
                .filter(
                    OrganizationMember.organization_id == workspace.organization_id,
                    OrganizationMember.role == role_required,
                )
                .all()
            )
            
            for member in org_members:
                user = db.query(User).filter(User.id == member.user_id).first()
                if user and user not in users:
                    users.append(user)
    
    return users


def _notify_requester(
    db: Session,
    approval: ContentApproval,
    status: str,
    comments: str | None = None,
) -> None:
    """Notify the requester of approval status change."""
    requester = db.query(User).filter(User.id == approval.requested_by).first()
    if not requester:
        return
    
    # TODO: Send email notification
    # TODO: Send in-app notification
    
    logger.info(
        f"Approval status notification: Content {approval.content_id} "
        f"{status} - notifying {requester.email}"
    )
