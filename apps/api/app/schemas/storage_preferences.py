"""
Storage Preferences schemas for granular storage control.

Allows users to specify where different types of content should be stored:
- google_drive: User's Google Drive (privacy-first, user owns the data)
- local: Download to local machine
- iterra: Stored on Iterra servers (with encryption)
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class StorageType(str):
    """Storage location types."""

    GOOGLE_DRIVE = "google_drive"
    LOCAL = "local"
    ITERRA = "iterra"


class StoragePreferences(BaseModel):
    """
    Granular storage preferences for different content types.

    Each content type can have its own storage location:
    - default: Default storage for unspecified content types
    - drafts: Content drafts
    - analysis: AI-generated analysis (brand profile, post analysis)
    - scraped_posts: Data scraped from social platforms
    - calendar: Content calendar and plans
    - reports: Generated reports and exports
    """

    default: str = Field(
        default="google_drive",
        description="Default storage location for unspecified content types",
    )
    drafts: Optional[str] = Field(
        default=None,
        description="Storage for content drafts",
    )
    analysis: Optional[str] = Field(
        default=None,
        description="Storage for AI analysis data",
    )
    scraped_posts: Optional[str] = Field(
        default=None,
        description="Storage for scraped social media posts",
    )
    calendar: Optional[str] = Field(
        default=None,
        description="Storage for content calendar data",
    )
    reports: Optional[str] = Field(
        default=None,
        description="Storage for generated reports",
    )
    analytics: Optional[str] = Field(
        default=None,
        description="Storage for analytics data",
    )

    @field_validator("default", "drafts", "analysis", "scraped_posts", "calendar", "reports", "analytics")
    @classmethod
    def validate_storage_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that storage type is one of the allowed values."""
        if v is None:
            return v

        allowed = {"google_drive", "local", "ittera"}
        if v not in allowed:
            raise ValueError(f"Storage type must be one of: {allowed}")
        return v

    def get_for_type(self, content_type: str) -> str:
        """
        Get the storage location for a specific content type.

        Args:
            content_type: Type of content (drafts, analysis, etc.)

        Returns:
            Storage location (google_drive, local, or iterra)
        """
        # Check if specific setting exists for this content type
        specific = getattr(self, content_type, None)
        if specific:
            return specific

        # Fall back to default
        return self.default

    def is_drive_enabled(self, content_type: Optional[str] = None) -> bool:
        """
        Check if Google Drive is enabled for a content type.

        Args:
            content_type: Optional specific content type to check

        Returns:
            True if Drive is enabled for the content type
        """
        storage = self.get_for_type(content_type or "default")
        return storage == "google_drive"


class StoragePreferencesUpdate(BaseModel):
    """Schema for updating storage preferences."""

    default: Optional[str] = None
    drafts: Optional[str] = None
    analysis: Optional[str] = None
    scraped_posts: Optional[str] = None
    calendar: Optional[str] = None
    reports: Optional[str] = None
    analytics: Optional[str] = None
    data_retention_days: Optional[int] = Field(
        default=None,
        description="Data retention policy in days (0 = never delete, null = default)",
    )

    @field_validator("default", "drafts", "analysis", "scraped_posts", "calendar", "reports", "analytics")
    @classmethod
    def validate_storage_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate that storage type is one of the allowed values."""
        if v is None:
            return v

        allowed = {"google_drive", "local", "ittera"}
        if v not in allowed:
            raise ValueError(f"Storage type must be one of: {allowed}")
        return v


class StoragePreferencesResponse(BaseModel):
    """Response schema for storage preferences."""

    preferences: StoragePreferences
    data_retention_days: Optional[int]
    message: str = "Storage preferences retrieved successfully"


class StoragePreferencesUpdateResponse(BaseModel):
    """Response schema after updating storage preferences."""

    preferences: StoragePreferences
    data_retention_days: Optional[int]
    message: str = "Storage preferences updated successfully"


class DataRetentionPolicy(BaseModel):
    """Data retention policy settings."""

    days: Optional[int] = Field(
        default=None,
        description="Retention period in days (null = system default, 0 = never delete)",
    )
    auto_delete_enabled: bool = Field(
        default=False,
        description="Whether auto-deletion is enabled",
    )
    description: str = Field(
        default="",
        description="Human-readable description of the retention policy",
    )

    @field_validator("days")
    @classmethod
    def validate_days(cls, v: Optional[int]) -> Optional[int]:
        """Validate retention days."""
        if v is None:
            return v
        if v < 0:
            raise ValueError("Retention days must be 0 or greater (0 = never delete)")
        if v > 3650:  # 10 years max
            raise ValueError("Retention days cannot exceed 3650 (10 years)")
        return v
