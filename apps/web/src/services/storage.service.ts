/**
 * Storage Service — API client for storage management.
 *
 * Handles:
 * - Google Drive connection status
 * - Storage preferences
 * - Data export/import
 * - Privacy dashboard
 * - GDPR data deletion
 */

import { apiFetch } from "./api";

export interface StorageStatus {
  connected: boolean;
  iterra_folder_id?: string;
  drafts_folder_id?: string;
  scraped_posts_file_id?: string;
  brand_analysis_file_id?: string;
}

export interface StorageHealth {
  healthy: boolean;
  connected: boolean;
  can_read: boolean;
  can_write: boolean;
  scopes_valid: boolean;
  message: string;
  last_checked?: string;
}

export interface StorageFileInfo {
  id: string;
  name: string;
  mime_type?: string;
  size?: string;
  modified_at?: string;
}

export interface StorageExportResponse {
  files: StorageFileInfo[];
  total: number;
  message: string;
}

export interface StoragePreferences {
  default: "google_drive" | "local" | "ittera";
  drafts?: "google_drive" | "local" | "ittera";
  analysis?: "google_drive" | "local" | "ittera";
  scraped_posts?: "google_drive" | "local" | "ittera";
  calendar?: "google_drive" | "local" | "ittera";
  reports?: "google_drive" | "local" | "ittera";
  analytics?: "google_drive" | "local" | "ittera";
}

export interface DataRetentionPolicy {
  days: number | null;
  auto_delete_enabled: boolean;
}

export interface PrivacyDashboard {
  user_id: string;
  generated_at: string;
  data_locations: DataLocationInfo[];
  drive_connected: boolean;
  drive_folder_id?: string;
  storage_preferences: StoragePreferences;
  data_retention_days: number | null;
  next_cleanup_date?: string;
  recent_exports: Array<{
    timestamp: string;
    file_count: number;
  }>;
  last_accessed?: string;
  pending_operations: number;
  can_export: boolean;
  can_delete: boolean;
  message: string;
}

export interface DataLocationInfo {
  data_type: string;
  storage_location: "google_drive" | "iterra_db" | "both" | "none";
  description: string;
  drive_file_id?: string;
  last_updated?: string;
  size_approximate?: string;
}

export interface DataExportDownload {
  export_data: Record<string, unknown>;
  export_timestamp: string;
  total_files: number;
  total_drafts: number;
  message: string;
}

export interface DataImportResult {
  success: boolean;
  scraped_posts_imported: boolean;
  brand_analysis_imported: boolean;
  drafts_imported: number;
  drafts_skipped: number;
  errors: string[];
  import_timestamp: string;
  message: string;
}

export interface DeleteDataResponse {
  deleted_files: number;
  db_records_cleared: boolean;
  message: string;
}

export const storageService = {
  /**
   * Get Google Drive connection status.
   */
  async getStatus(): Promise<StorageStatus> {
    return apiFetch<StorageStatus>("/api/v1/storage/status");
  },

  /**
   * Check Drive connection health.
   */
  async checkHealth(): Promise<StorageHealth> {
    return apiFetch<StorageHealth>("/api/v1/storage/health");
  },

  /**
   * List all Iterra files in user's Drive.
   */
  async listFiles(): Promise<StorageExportResponse> {
    return apiFetch<StorageExportResponse>("/api/v1/storage/export");
  },

  /**
   * Get privacy dashboard data.
   */
  async getPrivacyDashboard(): Promise<PrivacyDashboard> {
    return apiFetch<PrivacyDashboard>("/api/v1/storage/privacy-dashboard");
  },

  /**
   * Get storage preferences.
   */
  async getPreferences(): Promise<StoragePreferences> {
    return apiFetch<StoragePreferences>("/api/v1/users/me/storage-preferences");
  },

  /**
   * Update storage preferences.
   */
  async updatePreferences(
    preferences: Partial<StoragePreferences>,
    dataRetentionDays?: number | null
  ): Promise<{ preferences: StoragePreferences; data_retention_days: number | null }> {
    return apiFetch<{ preferences: StoragePreferences; data_retention_days: number | null }>(
      "/api/v1/users/me/storage-preferences",
      {
        method: "PUT",
        body: JSON.stringify({
          preferences,
          data_retention_days: dataRetentionDays,
        }),
      }
    );
  },

  /**
   * Export all data (GDPR Article 20 - data portability).
   */
  async exportAllData(): Promise<DataExportDownload> {
    return apiFetch<DataExportDownload>("/api/v1/storage/export/download");
  },

  /**
   * Import data from a previous export.
   */
  async importData(data: Record<string, unknown>, overwrite = false): Promise<DataImportResult> {
    const params = new URLSearchParams({ overwrite: String(overwrite) });
    return apiFetch<DataImportResult>(`/api/v1/storage/import?${params}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete all data (GDPR Article 17 - right to erasure).
   * WARNING: This is irreversible!
   */
  async deleteAllData(): Promise<DeleteDataResponse> {
    return apiFetch<DeleteDataResponse>("/api/v1/storage/data", { method: "DELETE" });
  },

  /**
   * Get Google Drive OAuth URL for connecting.
   */
  async getConnectUrl(): Promise<string> {
    const response = await apiFetch<{ authorization_url: string }>("/api/v1/social/connect/google-drive");
    return response.authorization_url;
  },
};
