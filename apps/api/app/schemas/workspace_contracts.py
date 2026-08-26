"""Versioned contracts shared by tenancy producers and the web workspace shell."""

from typing import Literal

from pydantic import BaseModel, Field


ContractAvailability = Literal["available", "degraded", "unavailable"]


class WorkspaceSummaryV1(BaseModel):
    """Developer A-owned workspace identity consumed by Developer B."""

    schema_version: Literal["workspace-summary.v1"] = "workspace-summary.v1"
    availability: ContractAvailability = "available"
    reason: str | None = None
    id: str
    organization_id: str
    organization_name: str
    name: str
    slug: str
    is_active: bool


class BrandSummaryV1(BaseModel):
    """Developer A-owned brand summary with an explicit degraded state."""

    schema_version: Literal["brand-summary.v1"] = "brand-summary.v1"
    availability: ContractAvailability
    reason: str | None = None
    id: str | None = None
    workspace_id: str
    name: str
    profile_version: int | None = None
    brand_colors: dict[str, str] = Field(default_factory=dict)
    logo_url: str | None = None


class WhiteLabelSummaryV1(BaseModel):
    """Stable presentation subset; raw organization settings stay internal."""

    schema_version: Literal["white-label-summary.v1"] = "white-label-summary.v1"
    availability: ContractAvailability = "available"
    reason: str | None = None
    enabled: bool
    primary_color: str | None = None
    secondary_color: str | None = None
    logo_url: str | None = None
    sender_name: str | None = None
    hide_powered_by: bool = False


class AuthorizationContextV1(BaseModel):
    """Developer A-owned authorization contract consumed by Developer B."""

    schema_version: Literal["authorization-context.v1"] = "authorization-context.v1"
    availability: ContractAvailability = "available"
    reason: str | None = None
    workspace: WorkspaceSummaryV1
    brand: BrandSummaryV1
    role: str
    permissions: list[str]
    white_label: WhiteLabelSummaryV1
