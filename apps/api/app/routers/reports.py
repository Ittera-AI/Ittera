"""Report generation and delivery API endpoints.

Provides endpoints for:
- On-demand PDF report generation
- Scheduled report configuration
- Report history and download
- Email delivery
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.permissions import Permission
from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.workspace import (
    can_create_reports,
    can_use_whitelabel,
    get_current_workspace,
)
from app.models.organization import Workspace
from app.models.user import User
from app.services import reporting_service, workspace_service

router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Request/Response Schemas
# ---------------------------------------------------------------------------

class ReportType(str):
    ANALYTICS = "analytics"
    COMPETITIVE = "competitive"
    CUSTOM = "custom"


class AnalyticsReportRequest(BaseModel):
    """Request to generate an analytics report."""
    period_days: int = Field(default=30, ge=7, le=365)
    include_charts: bool = Field(default=True)
    email_recipients: list[str] = Field(default_factory=list)
    send_email: bool = Field(default=False)


class CompetitiveReportRequest(BaseModel):
    """Request to generate a competitive intelligence report."""
    analysis_id: str | None = Field(
        None,
        description="Specific analysis to include, or latest if not provided",
    )
    email_recipients: list[str] = Field(default_factory=list)
    send_email: bool = Field(default=False)


class CustomReportSection(BaseModel):
    """Custom report section definition."""
    type: Literal["metrics", "table", "text", "insights"] = Field(...)
    title: str = Field(..., min_length=1, max_length=200)
    data: dict = Field(default_factory=dict)


class CustomReportRequest(BaseModel):
    """Request to generate a custom report."""
    title: str = Field(..., min_length=1, max_length=200)
    sections: list[CustomReportSection] = Field(..., min_length=1)
    email_recipients: list[str] = Field(default_factory=list)
    send_email: bool = Field(default=False)


class ReportResponse(BaseModel):
    """Report generation response."""
    report_id: str
    report_type: str
    download_url: str | None
    status: Literal["generated", "queued", "error"]
    metadata: dict
    message: str | None


class ReportMetadata(BaseModel):
    """Report metadata for listing."""
    report_id: str
    report_type: str
    title: str | None
    generated_at: str
    size_kb: float
    download_url: str


class ScheduledReportConfig(BaseModel):
    """Configuration for scheduled reports."""
    report_type: Literal["analytics", "competitive"] = "analytics"
    frequency: Literal["weekly", "monthly", "quarterly"] = "monthly"
    period_days: int = Field(default=30, ge=7, le=365)
    email_recipients: list[str] = Field(default_factory=list)
    include_charts: bool = Field(default=True)
    day_of_week: int | None = Field(None, ge=0, le=6)  # For weekly
    day_of_month: int | None = Field(None, ge=1, le=31)  # For monthly


class WhiteLabelSettingsResponse(BaseModel):
    """White-label settings for reports."""
    enabled: bool
    logo_url: str | None
    primary_color: str
    secondary_color: str | None
    sender_name: str
    sender_email: str
    custom_footer: str | None
    hide_powered_by: bool


class WhiteLabelSettingsUpdate(BaseModel):
    """Update white-label settings."""
    enabled: bool | None = None
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sender_name: str | None = None
    sender_email: str | None = None
    custom_footer: str | None = None
    hide_powered_by: bool | None = None


# In-memory report storage (replace with database/S3 in production)
_report_storage: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Report Generation Endpoints
# ---------------------------------------------------------------------------

def _store_report(
    report_id: str,
    report_type: str,
    pdf_bytes: bytes,
    user_id: str,
    workspace_id: str | None,
) -> str:
    """Store report and return download URL."""
    import hashlib
    
    # In production, upload to S3/cloud storage
    # For now, store in memory
    _report_storage[report_id] = {
        "pdf_bytes": pdf_bytes,
        "type": report_type,
        "user_id": user_id,
        "workspace_id": workspace_id,
        "generated_at": datetime.now().isoformat(),
        "size_kb": round(len(pdf_bytes) / 1024, 1),
    }
    
    return f"/api/v1/reports/download/{report_id}"


@router.post("/analytics", response_model=ReportResponse)
async def generate_analytics_report(
    request: AnalyticsReportRequest,
    workspace: Workspace | None = Depends(can_create_reports),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an analytics PDF report.
    
    Comprehensive report including:
    - Performance metrics and trends
    - Engagement analysis
    - AI-generated insights
    - Top performing content
    """
    try:
        pdf_bytes = reporting_service.generate_analytics_report(
            db=db,
            user=current_user,
            workspace=workspace,
            period_days=request.period_days,
            include_charts=request.include_charts,
        )
        
        report_id = f"analytics_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id[:8]}"
        download_url = _store_report(
            report_id=report_id,
            report_type="analytics",
            pdf_bytes=pdf_bytes,
            user_id=current_user.id,
            workspace_id=workspace.id if workspace else None,
        )
        
        # TODO: Send email if requested
        if request.send_email and request.email_recipients:
            # Queue email delivery task
            pass
        
        return {
            "report_id": report_id,
            "report_type": "analytics",
            "download_url": download_url,
            "status": "generated",
            "metadata": {
                "size_kb": round(len(pdf_bytes) / 1024, 1),
                "period_days": request.period_days,
            },
            "message": None,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.post("/competitive", response_model=ReportResponse)
async def generate_competitive_report(
    request: CompetitiveReportRequest,
    workspace: Workspace | None = Depends(can_create_reports),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a competitive intelligence PDF report.
    
    Includes:
    - Competitor overview
    - Content gap analysis
    - Strategic opportunities
    - Actionable recommendations
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competitive reports require workspace context",
        )
    
    try:
        pdf_bytes = reporting_service.generate_competitive_report(
            db=db,
            user=current_user,
            workspace=workspace,
            analysis_id=request.analysis_id,
        )
        
        report_id = f"competitive_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id[:8]}"
        download_url = _store_report(
            report_id=report_id,
            report_type="competitive",
            pdf_bytes=pdf_bytes,
            user_id=current_user.id,
            workspace_id=workspace.id,
        )
        
        return {
            "report_id": report_id,
            "report_type": "competitive",
            "download_url": download_url,
            "status": "generated",
            "metadata": {
                "size_kb": round(len(pdf_bytes) / 1024, 1),
            },
            "message": None,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.post("/custom", response_model=ReportResponse)
async def generate_custom_report(
    request: CustomReportRequest,
    workspace: Workspace | None = Depends(can_create_reports),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a custom PDF report from structured sections.
    
    Allows building reports with:
    - Metric cards
    - Data tables
    - Text blocks
    - Insight boxes
    """
    try:
        # Convert sections to dict format
        sections = [s.model_dump() for s in request.sections]
        
        pdf_bytes = reporting_service.generate_custom_report(
            title=request.title,
            sections=sections,
            workspace=workspace,
            organization=workspace.organization if workspace else None,
        )
        
        report_id = f"custom_{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id[:8]}"
        download_url = _store_report(
            report_id=report_id,
            report_type="custom",
            pdf_bytes=pdf_bytes,
            user_id=current_user.id,
            workspace_id=workspace.id if workspace else None,
        )
        
        return {
            "report_id": report_id,
            "report_type": "custom",
            "download_url": download_url,
            "status": "generated",
            "metadata": {
                "size_kb": round(len(pdf_bytes) / 1024, 1),
                "section_count": len(request.sections),
            },
            "message": None,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Report Download
# ---------------------------------------------------------------------------

@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download a generated report by ID."""
    report = _report_storage.get(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Owner-scoped access (R2.2): a report that does not belong to the
    # authenticated user is indistinguishable from a missing report — return
    # 404 rather than 403 so we never disclose the existence of another user's
    # report by identifier.
    if report["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return Response(
        content=report["pdf_bytes"],
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report_{report_id}.pdf"',
            "Content-Length": str(len(report["pdf_bytes"])),
        },
    )


@router.get("/history", response_model=list[ReportMetadata])
async def list_reports(
    report_type: Literal["analytics", "competitive", "custom", "all"] = "all",
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """List generated reports for the user."""
    reports = []
    
    for report_id, report in _report_storage.items():
        if report["user_id"] != current_user.id:
            continue
        
        if report_type != "all" and report["type"] != report_type:
            continue
        
        reports.append({
            "report_id": report_id,
            "report_type": report["type"],
            "title": None,  # Could extract from PDF metadata
            "generated_at": report["generated_at"],
            "size_kb": report["size_kb"],
            "download_url": f"/api/v1/reports/download/{report_id}",
        })
    
    # Sort by date (newest first)
    reports.sort(key=lambda x: x["generated_at"], reverse=True)
    
    return reports[:limit]


# ---------------------------------------------------------------------------
# White-Label Settings
# ---------------------------------------------------------------------------

@router.get("/white-label", response_model=WhiteLabelSettingsResponse)
async def get_white_label_settings(
    workspace: Workspace | None = Depends(can_use_whitelabel),
):
    """
    Get white-label settings for reports.
    
    Used to customize report branding, colors, and sender information.
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required for white-label settings",
        )
    
    org = workspace.organization
    settings = reporting_service.get_brand_settings(workspace, org)
    
    # Convert to response format
    wl = org.white_label_settings or {} if org else {}
    
    return {
        "enabled": wl.get("enabled", False),
        "logo_url": settings.get("logo_url"),
        "primary_color": settings.get("brand_color", "#6366F1"),
        "secondary_color": wl.get("secondary_color"),
        "sender_name": wl.get("sender_name", "Iterra Reports"),
        "sender_email": wl.get("sender_email", "reports@iterra.io"),
        "custom_footer": wl.get("custom_footer"),
        "hide_powered_by": wl.get("hide_powered_by", False),
    }


@router.patch("/white-label", response_model=WhiteLabelSettingsResponse)
async def update_white_label_settings(
    request: WhiteLabelSettingsUpdate,
    workspace: Workspace | None = Depends(can_use_whitelabel),
    db: Session = Depends(get_db),
):
    """
    Update white-label settings for reports.
    
    Allows customizing:
    - Brand colors
    - Logo
    - Sender information
    - Footer text
    """
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context required",
        )
    
    org = workspace.organization
    if not org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found",
        )
    
    # Convert to service format
    update_data = {
        "enabled": request.enabled,
        "logo_url": request.logo_url,
        "primary_color": request.primary_color,
        "secondary_color": request.secondary_color,
        "sender_name": request.sender_name,
        "sender_email": request.sender_email,
        "custom_footer": request.custom_footer,
        "hide_powered_by": request.hide_powered_by,
    }
    
    # Remove None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    updated_settings = workspace_service.update_white_label_settings(
        db, org, update_data
    )
    
    return {
        "enabled": updated_settings.get("enabled", False),
        "logo_url": updated_settings.get("logo_url"),
        "primary_color": updated_settings.get("primary_color", "#6366F1"),
        "secondary_color": updated_settings.get("secondary_color"),
        "sender_name": updated_settings.get("sender_name", "Iterra Reports"),
        "sender_email": updated_settings.get("sender_email", "reports@iterra.io"),
        "custom_footer": updated_settings.get("custom_footer"),
        "hide_powered_by": updated_settings.get("hide_powered_by", False),
    }


# ---------------------------------------------------------------------------
# Scheduled Reports
# ---------------------------------------------------------------------------

@router.post("/scheduled")
async def configure_scheduled_report(
    request: ScheduledReportConfig,
    workspace: Workspace | None = Depends(can_create_reports),
    current_user: User = Depends(get_current_user),
):
    """
    Configure automated scheduled reports.
    
    Schedule regular analytics or competitive reports to be
    generated and emailed automatically.
    """
    # TODO: Store in database and set up Celery beat schedule
    # For now, return configuration received
    
    return {
        "status": "configured",
        "configuration": request.model_dump(),
        "message": "Scheduled reports are being set up. You will receive a confirmation email.",
    }


@router.get("/scheduled")
async def list_scheduled_reports(
    workspace: Workspace | None = Depends(can_create_reports),
    current_user: User = Depends(get_current_user),
):
    """List configured scheduled reports."""
    # TODO: Query database for scheduled reports
    return {
        "scheduled_reports": [],
        "message": "Scheduled report listing coming soon",
    }
