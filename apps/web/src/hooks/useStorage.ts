/**
 * useStorage hook — manages storage state and operations.
 *
 * Provides:
 * - Storage connection status
 * - Storage preferences management
 * - Data export/import
 * - Privacy dashboard data
 */

import { useCallback, useEffect, useState } from "react";

import { storageService, StorageStatus, StorageHealth, StoragePreferences, PrivacyDashboard } from "@/services/storage.service";

interface UseStorageReturn {
  // Status
  status: StorageStatus | null;
  health: StorageHealth | null;
  dashboard: PrivacyDashboard | null;
  preferences: StoragePreferences | null;

  // Loading states
  isLoading: boolean;
  isUpdating: boolean;
  isExporting: boolean;
  isDeleting: boolean;

  // Errors
  error: string | null;

  // Actions
  refreshStatus: () => Promise<void>;
  refreshHealth: () => Promise<void>;
  refreshDashboard: () => Promise<void>;
  updatePreferences: (preferences: Partial<StoragePreferences>, dataRetentionDays?: number | null) => Promise<void>;
  exportData: () => Promise<Record<string, unknown> | null>;
  importData: (data: Record<string, unknown>, overwrite?: boolean) => Promise<boolean>;
  deleteAllData: () => Promise<boolean>;
  connectDrive: () => Promise<void>;
}

export function useStorage(): UseStorageReturn {
  // State
  const [status, setStatus] = useState<StorageStatus | null>(null);
  const [health, setHealth] = useState<StorageHealth | null>(null);
  const [dashboard, setDashboard] = useState<PrivacyDashboard | null>(null);
  const [preferences, setPreferences] = useState<StoragePreferences | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch status
  const refreshStatus = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await storageService.getStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load storage status");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch health
  const refreshHealth = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await storageService.checkHealth();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check storage health");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch dashboard
  const refreshDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await storageService.getPrivacyDashboard();
      setDashboard(data);
      setPreferences(data.storage_preferences);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load privacy dashboard");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Update preferences
  const updatePreferences = useCallback(async (
    newPreferences: Partial<StoragePreferences>,
    dataRetentionDays?: number | null
  ) => {
    setIsUpdating(true);
    setError(null);
    try {
      const result = await storageService.updatePreferences(newPreferences, dataRetentionDays);
      setPreferences(result.preferences);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update preferences");
      throw err;
    } finally {
      setIsUpdating(false);
    }
  }, []);

  // Export data
  const exportData = useCallback(async (): Promise<Record<string, unknown> | null> => {
    setIsExporting(true);
    setError(null);
    try {
      const result = await storageService.exportAllData();
      // Create and download JSON file
      const blob = new Blob([JSON.stringify(result.export_data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `iterra-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      return result.export_data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to export data");
      return null;
    } finally {
      setIsExporting(false);
    }
  }, []);

  // Import data
  const importData = useCallback(async (data: Record<string, unknown>, overwrite = false): Promise<boolean> => {
    setIsUpdating(true);
    setError(null);
    try {
      const result = await storageService.importData(data, overwrite);
      return result.success;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to import data");
      return false;
    } finally {
      setIsUpdating(false);
    }
  }, []);

  // Delete all data
  const deleteAllData = useCallback(async (): Promise<boolean> => {
    setIsDeleting(true);
    setError(null);
    try {
      await storageService.deleteAllData();
      // Refresh status after deletion
      await refreshStatus();
      await refreshDashboard();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete data");
      return false;
    } finally {
      setIsDeleting(false);
    }
  }, [refreshStatus, refreshDashboard]);

  // Connect Drive
  const connectDrive = useCallback(async () => {
    try {
      const url = await storageService.getConnectUrl();
      // Open OAuth in same window (will redirect back)
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get connect URL");
    }
  }, []);

  // Initial load
  useEffect(() => {
    refreshStatus();
    refreshDashboard();
  }, [refreshStatus, refreshDashboard]);

  return {
    // Status
    status,
    health,
    dashboard,
    preferences,

    // Loading states
    isLoading,
    isUpdating,
    isExporting,
    isDeleting,

    // Errors
    error,

    // Actions
    refreshStatus,
    refreshHealth,
    refreshDashboard,
    updatePreferences,
    exportData,
    importData,
    deleteAllData,
    connectDrive,
  };
}
