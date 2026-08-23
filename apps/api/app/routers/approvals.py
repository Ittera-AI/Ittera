"""Approval Workflow API endpoints.

Provides endpoints for:
- Managing approval workflows
- Requesting approvals for content
- Making approval decisions
- Tracking approval status
- Viewing pending approvals
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.workspace import (
    can_manage_workspace,
    get_required_current_workspace,
)
from app.models.organization import ApprovalWorkflow, ContentApproval, Workspace
from app.models.user import User
from app.services import approval_service

router = APIRouter(tags=["approvals"])


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class WorkflowStep(BaseModel):
    step_number: int = Field(..., ge=1)
    role_required: str | None = None
    user_id: str | None = None
    title: str
    description: str | None = None
    can_edit: bool = Field(default=False)
    auto_approve_hours: int | None = Field(None, ge=1, le=168)


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    content_type: Literal["post", "content_plan", "campaign"] = "post"
    steps: list[WorkflowStep] = Field(..., min_length=1)


class WorkflowResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    content_type: str
    steps: list[dict]
    is_active: bool
    created_at: str
    
    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    content_type: str
    content_id: str
    workflow_id: str | None = None
    note: str | None = None


class ApprovalDecisionRequest(BaseModel):
    expected_step: int = Field(..., ge=0)
    decision: Literal["approved", "rejected", "requested_changes"]
    comments: str | None = Field(None, max_length=2000)


class ResubmitRequest(BaseModel):
    change_notes: str | None = None


class ApprovalResponse(BaseModel):
    id: str
    workspace_id: str
    content_type: str
    content_id: str
    workflow_id: str | None
    current_step: int
    status: str
    requested_by: str
    requested_at: datetime
    completed_at: datetime | None
    
    class Config:
        from_attributes = True


class ApprovalDetailResponse(ApprovalResponse):
    workflow_name: str | None
    current_step_title: str | None
    decisions: list[dict]
    can_approve: bool = False


class PendingApprovalsResponse(BaseModel):
    pending: list[ApprovalDetailResponse]
    total: int


class MyApprovalsResponse(BaseModel):
    requested: list[ApprovalResponse]
    pending_my_decision: list[ApprovalDetailResponse]


# ---------------------------------------------------------------------------
# Workflow Management
# ---------------------------------------------------------------------------

@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(
    workspace: Workspace | None = Depends(get_required_current_workspace),
    db: Session = Depends(get_db),
):
    """List all approval workflows for the workspace."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    workflows = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.workspace_id == workspace.id)
        .all()
    )
    
    return workflows


@router.post("/workflows", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    data: WorkflowCreate,
    workspace: Workspace | None = Depends(can_manage_workspace),
    db: Session = Depends(get_db),
):
    """
    Create a new approval workflow.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    workflow = approval_service.create_workflow(
        db=db,
        workspace=workspace,
        name=data.name,
        content_type=data.content_type,
        steps=[step.model_dump() for step in data.steps],
    )
    
    return workflow


@router.patch("/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    data: dict,
    workspace: Workspace | None = Depends(can_manage_workspace),
    db: Session = Depends(get_db),
):
    """
    Update an approval workflow.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    workflow = (
        db.query(ApprovalWorkflow)
        .filter(
            ApprovalWorkflow.id == workflow_id,
            ApprovalWorkflow.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update allowed fields
    if "name" in data:
        workflow.name = data["name"]
    if "steps" in data:
        workflow.steps = data["steps"]
    if "is_active" in data:
        workflow.is_active = data["is_active"]
    
    db.commit()
    db.refresh(workflow)
    
    return workflow


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    workspace: Workspace | None = Depends(can_manage_workspace),
    db: Session = Depends(get_db),
):
    """
    Soft-delete an approval workflow.
    
    Requires: workspace:manage permission
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    workflow = (
        db.query(ApprovalWorkflow)
        .filter(
            ApprovalWorkflow.id == workflow_id,
            ApprovalWorkflow.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow.is_active = False
    db.commit()
    
    return None


# ---------------------------------------------------------------------------
# Approval Actions
# ---------------------------------------------------------------------------

@router.post("/request", response_model=ApprovalResponse)
async def request_approval(
    data: ApprovalRequest,
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request approval for content.
    
    Starts the approval workflow for the specified content.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    approval = approval_service.request_approval(
        db=db,
        workspace=workspace,
        content_type=data.content_type,
        content_id=data.content_id,
        workflow_id=data.workflow_id,
        requested_by=current_user,
        note=data.note,
    )
    
    return approval


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
async def make_decision(
    approval_id: str,
    data: ApprovalDecisionRequest,
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Make an approval decision.
    
    Decisions: approved, rejected, requested_changes
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    approval = (
        db.query(ContentApproval)
        .filter(
            ContentApproval.id == approval_id,
            ContentApproval.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval = approval_service.make_decision(
        db=db,
        approval=approval,
        approver=current_user,
        expected_step=data.expected_step,
        decision=data.decision,
        comments=data.comments,
    )
    
    return approval


@router.post("/{approval_id}/resubmit", response_model=ApprovalResponse)
async def resubmit_after_changes(
    approval_id: str,
    data: ResubmitRequest,
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resubmit content after changes were requested.
    
    Returns the approval to pending status for re-review.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    approval = (
        db.query(ContentApproval)
        .filter(
            ContentApproval.id == approval_id,
            ContentApproval.workspace_id == workspace.id,
            ContentApproval.requested_by == current_user.id,
        )
        .first()
    )
    
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    if approval.status != "changes_requested":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is not in changes_requested status",
        )
    
    approval = approval_service.resubmit_after_changes(
        db=db,
        approval=approval,
        requester=current_user,
        change_notes=data.change_notes,
    )
    
    return approval


# ---------------------------------------------------------------------------
# Status and Queries
# ---------------------------------------------------------------------------

@router.get("/status/{content_type}/{content_id}", response_model=ApprovalDetailResponse)
async def get_approval_status(
    content_type: str,
    content_id: str,
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get approval status for specific content."""
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    approval = approval_service.get_approval_status(
        db=db,
        workspace_id=workspace.id,
        content_type=content_type,
        content_id=content_id,
    )

    if not approval:
        raise HTTPException(status_code=404, detail="No approval found for this content")
    
    # Get workflow details
    workflow = db.query(ApprovalWorkflow).filter(
        ApprovalWorkflow.id == approval.workflow_id
    ).first()
    
    # Check if current user can approve
    can_approve = False
    if approval.status == "pending" and workflow:
        steps = workflow.steps or []
        if approval.current_step < len(steps):
            current_step = steps[approval.current_step]
            can_approve = approval_service._user_can_approve_step(
                db, current_user, workspace.id, current_step
            )
    
    # Build response
    decisions = [
        {
            "step_number": d.step_number,
            "decision": d.decision,
            "comments": d.comments,
            "decided_at": d.decided_at.isoformat() if d.decided_at else None,
        }
        for d in approval.decisions
    ]
    
    current_step_title = None
    if workflow and workflow.steps and approval.current_step < len(workflow.steps):
        current_step_title = workflow.steps[approval.current_step].get("title")
    
    return {
        "id": approval.id,
        "workspace_id": approval.workspace_id,
        "content_type": approval.content_type,
        "content_id": approval.content_id,
        "workflow_id": approval.workflow_id,
        "current_step": approval.current_step,
        "status": approval.status,
        "requested_by": approval.requested_by,
        "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
        "completed_at": approval.completed_at.isoformat() if approval.completed_at else None,
        "workflow_name": workflow.name if workflow else None,
        "current_step_title": current_step_title,
        "decisions": decisions,
        "can_approve": can_approve,
    }


@router.get("/pending", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get pending approvals awaiting this user's decision.
    
    Shows only approvals where the user is the current approver.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    pending = approval_service.get_pending_approvals_for_user(
        db=db,
        user=current_user,
        workspace_ids=[workspace.id],
    )
    
    # Enhance with details
    results = []
    for approval in pending:
        workflow = db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == approval.workflow_id
        ).first()
        
        current_step_title = None
        if workflow and workflow.steps and approval.current_step < len(workflow.steps):
            current_step_title = workflow.steps[approval.current_step].get("title")
        
        results.append({
            "id": approval.id,
            "workspace_id": approval.workspace_id,
            "content_type": approval.content_type,
            "content_id": approval.content_id,
            "workflow_id": approval.workflow_id,
            "current_step": approval.current_step,
            "status": approval.status,
            "requested_by": approval.requested_by,
            "requested_at": approval.requested_at.isoformat() if approval.requested_at else None,
            "completed_at": approval.completed_at.isoformat() if approval.completed_at else None,
            "workflow_name": workflow.name if workflow else None,
            "current_step_title": current_step_title,
            "decisions": [],
            "can_approve": True,  # By definition, if it's in this list
        })
    
    return {
        "pending": results,
        "total": len(results),
    }


@router.get("/my", response_model=MyApprovalsResponse)
async def get_my_approvals(
    workspace: Workspace | None = Depends(get_required_current_workspace),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all approvals related to the current user.
    
    Includes:
    - Approvals requested by this user
    - Pending approvals awaiting this user's decision
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    # Get approvals requested by this user
    requested = (
        db.query(ContentApproval)
        .filter(
            ContentApproval.workspace_id == workspace.id,
            ContentApproval.requested_by == current_user.id,
        )
        .order_by(ContentApproval.requested_at.desc())
        .limit(20)
        .all()
    )
    
    # Get pending for this user
    pending = approval_service.get_pending_approvals_for_user(
        db=db,
        user=current_user,
        workspace_ids=[workspace.id],
    )
    
    return {
        "requested": [
            {
                "id": a.id,
                "workspace_id": a.workspace_id,
                "content_type": a.content_type,
                "content_id": a.content_id,
                "workflow_id": a.workflow_id,
                "current_step": a.current_step,
                "status": a.status,
                "requested_by": a.requested_by,
                "requested_at": a.requested_at.isoformat() if a.requested_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in requested
        ],
        "pending_my_decision": [
            {
                "id": a.id,
                "workspace_id": a.workspace_id,
                "content_type": a.content_type,
                "content_id": a.content_id,
                "workflow_id": a.workflow_id,
                "current_step": a.current_step,
                "status": a.status,
                "requested_by": a.requested_by,
                "requested_at": a.requested_at.isoformat() if a.requested_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "workflow_name": None,
                "current_step_title": None,
                "decisions": [],
                "can_approve": True,
            }
            for a in pending
        ],
    }
