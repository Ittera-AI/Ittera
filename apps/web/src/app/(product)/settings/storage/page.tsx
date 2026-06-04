"use client";

/**
 * Storage Settings Page
 *
 * Allows users to:
 * - View and manage Google Drive connection
 * - Set granular storage preferences per content type
 * - Configure data retention policies
 * - Export/import their data
 * - Delete all data (GDPR)
 */

import { useState } from "react";
import Link from "next/link";
import { ProductShell } from "@/components/product/ProductShell";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useStorage } from "@/hooks/useStorage";
import {
  CheckCircle,
  Cloud,
  Database,
  Download,
  ExternalLink,
  HardDrive,
  Loader2,
  Shield,
  Trash2,
  Upload,
  XCircle,
  ChevronLeft,
} from "lucide-react";

export default function StorageSettingsPage() {
  const {
    status,
    health,
    preferences,
    isLoading,
    isUpdating,
    isExporting,
    isDeleting,
    error,
    refreshHealth,
    updatePreferences,
    exportData,
    deleteAllData,
    connectDrive,
  } = useStorage();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [localPreferences, setLocalPreferences] = useState(preferences);

  // Update local preferences when they load
  if (preferences && !localPreferences) {
    setLocalPreferences(preferences);
  }

  const handlePreferenceChange = (
    contentType: string,
    value: "google_drive" | "local" | "ittera"
  ) => {
    if (!localPreferences) return;

    const updated = {
      ...localPreferences,
      [contentType]: value,
    };
    setLocalPreferences(updated);
    updatePreferences({ [contentType]: value });
  };

  const handleExport = async () => {
    await exportData();
  };

  const handleDeleteAll = async () => {
    if (deleteConfirmText !== "DELETE") return;
    const success = await deleteAllData();
    if (success) {
      setShowDeleteConfirm(false);
      setDeleteConfirmText("");
    }
  };

  const getHealthStatus = () => {
    if (!health) return null;

    if (health.healthy) {
      return (
        <div className="flex items-center gap-2 text-green-600">
          <CheckCircle className="h-5 w-5" />
          <span>Connected and healthy</span>
        </div>
      );
    }

    if (!health.connected) {
      return (
        <div className="flex items-center gap-2 text-amber-600">
          <XCircle className="h-5 w-5" />
          <span>Not connected</span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2 text-red-600">
        <XCircle className="h-5 w-5" />
        <span>{health.message}</span>
      </div>
    );
  };

  return (
    <ProductShell>
      <div className="mx-auto max-w-4xl space-y-8 pb-12">
        <div className="flex flex-col gap-6">
          <Link 
            href="/settings" 
            className="group flex w-fit items-center gap-2 rounded-lg pr-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted/50 transition-colors group-hover:bg-muted">
              <ChevronLeft className="h-4 w-4" />
            </div>
            Back to Settings
          </Link>
          
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Storage & Integrations</h1>
            <p className="text-muted-foreground text-sm">
              Manage your Google Workspace connection, data retention policies, and privacy settings.
            </p>
          </div>
        </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Google Workspace Connection (Premium UI) */}
      <div className="relative mb-8 group">
        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-blue-500/30 to-purple-500/30 opacity-20 blur transition duration-1000 group-hover:opacity-40 group-hover:duration-200" />
        <div className="relative rounded-xl border border-border/50 bg-card/80 p-6 backdrop-blur-xl shadow-sm transition-all hover:shadow-md overflow-hidden">
          {/* Subtle background glow based on status */}
          <div className={`absolute top-0 right-0 -mt-16 -mr-16 h-32 w-32 rounded-full blur-3xl opacity-20 ${status?.connected ? 'bg-green-500' : 'bg-blue-500'}`} />
          
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 relative z-10">
            
            {/* Left side: Header & Icon */}
            <div className="flex gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/20 text-blue-600 shadow-inner">
                <Cloud className="h-6 w-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-semibold tracking-tight text-foreground flex items-center gap-2">
                  Google Workspace
                  {status?.connected && health?.healthy && (
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                  )}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
                  Enable secure Google Drive backups and Calendar synchronization for automated content scheduling.
                </p>
              </div>
            </div>

            {/* Right side: Status & Actions */}
            <div className="w-full md:w-auto">
              {isLoading ? (
                <div className="flex h-10 items-center gap-2 rounded-lg border border-dashed px-4 py-2 text-sm text-muted-foreground bg-muted/10">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Verifying connection...</span>
                </div>
              ) : status?.connected ? (
                <div className="flex flex-col gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    {health?.healthy ? (
                      <div className="inline-flex items-center gap-1.5 rounded-full bg-green-500/10 px-2.5 py-1 text-xs font-medium text-green-600 dark:text-green-400 border border-green-500/20">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Connected & Healthy
                      </div>
                    ) : (
                      <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        <XCircle className="h-3.5 w-3.5" />
                        {health?.message || "Connection Issue"}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-1.5 text-xs">
                    <div className="flex items-center justify-between gap-4 rounded-md bg-muted/30 px-3 py-1.5 border border-border/50">
                      <span className="text-muted-foreground font-medium">Iterra Folder</span>
                      <code className="font-mono text-[10px] bg-background px-1.5 py-0.5 rounded border shadow-sm">
                        {status.iterra_folder_id?.slice(0, 12)}...
                      </code>
                    </div>
                    {status.drafts_folder_id && (
                      <div className="flex items-center justify-between gap-4 rounded-md bg-muted/30 px-3 py-1.5 border border-border/50">
                        <span className="text-muted-foreground font-medium">Drafts Folder</span>
                        <code className="font-mono text-[10px] bg-background px-1.5 py-0.5 rounded border shadow-sm">
                          {status.drafts_folder_id.slice(0, 12)}...
                        </code>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mt-2">
                    <Button variant="outline" size="sm" onClick={refreshHealth} className="h-8 text-xs font-medium transition-colors hover:bg-muted">
                      Check Health
                    </Button>
                    <a
                      href={`https://drive.google.com/drive/folders/${status.iterra_folder_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex h-8 items-center justify-center gap-1.5 rounded-md bg-blue-50 px-3 text-xs font-medium text-blue-600 transition-colors hover:bg-blue-100 dark:bg-blue-900/30 dark:hover:bg-blue-900/50"
                    >
                      Open Drive <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-start md:items-end gap-3">
                  <div className="inline-flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground border">
                    Not Connected
                  </div>
                  <Button 
                    onClick={connectDrive} 
                    className="flex items-center gap-2 shadow-sm transition-all hover:shadow-md bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 border-0 text-white group"
                  >
                    <Cloud className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:scale-110" />
                    Connect Google Workspace
                  </Button>
                </div>
              )}
            </div>
            
          </div>
        </div>
      </div>

      {/* Storage Preferences Premium UI */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden mb-8">
        <div className="border-b px-6 py-5 bg-muted/10">
          <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-500" />
            Storage Preferences
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Choose exactly where each type of content is physically stored.
          </p>
        </div>
        <div className="p-6">
          {localPreferences ? (
            <div className="space-y-8">
              {/* Default */}
              <div className="space-y-3">
                <Label className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Global Default Location</Label>
                <Select
                  value={localPreferences.default}
                  onValueChange={(v) =>
                    handlePreferenceChange("default", v as "google_drive" | "local" | "ittera")
                  }
                  disabled={isUpdating}
                >
                  <SelectTrigger className="w-full md:w-96 h-12 bg-background border-border/60 hover:bg-muted/30 transition-colors">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="google_drive">
                      <div className="flex items-center gap-2">
                        <Cloud className="h-4 w-4 text-blue-500" />
                        <span className="font-medium">Google Drive <span className="text-muted-foreground text-xs font-normal ml-1">(Recommended for Privacy)</span></span>
                      </div>
                    </SelectItem>
                    <SelectItem value="local">
                      <div className="flex items-center gap-2">
                        <HardDrive className="h-4 w-4 text-slate-500" />
                        <span className="font-medium">Local Download</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="ittera">
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-indigo-500" />
                        <span className="font-medium">Iterra Cloud</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator className="opacity-50" />

              {/* Per-type preferences */}
              <div className="space-y-4">
                <Label className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Granular Overrides</Label>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    { key: "drafts", label: "Content Drafts", icon: <Database className="h-4 w-4 opacity-50"/> },
                    { key: "analysis", label: "AI Analysis", icon: <Database className="h-4 w-4 opacity-50"/> },
                    { key: "scraped_posts", label: "Social Archives", icon: <Database className="h-4 w-4 opacity-50"/> },
                    { key: "calendar", label: "Content Calendar", icon: <Database className="h-4 w-4 opacity-50"/> },
                    { key: "reports", label: "Generated Reports", icon: <Database className="h-4 w-4 opacity-50"/> },
                    { key: "analytics", label: "Analytics Data", icon: <Database className="h-4 w-4 opacity-50"/> },
                  ].map(({ key, label, icon }) => (
                    <div key={key} className="space-y-2 rounded-lg border bg-muted/10 p-4 transition-colors hover:bg-muted/20">
                      <Label className="text-sm font-medium flex items-center gap-2 text-foreground">{icon} {label}</Label>
                      <Select
                        value={localPreferences[key as keyof typeof localPreferences] || localPreferences.default}
                        onValueChange={(v) =>
                          handlePreferenceChange(key, v as "google_drive" | "local" | "ittera")
                        }
                        disabled={isUpdating}
                      >
                        <SelectTrigger className="bg-background h-9 border-border/40">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="google_drive"><span className="flex items-center gap-2"><Cloud className="h-3 w-3"/> Google Drive</span></SelectItem>
                          <SelectItem value="local"><span className="flex items-center gap-2"><HardDrive className="h-3 w-3"/> Local</span></SelectItem>
                          <SelectItem value="ittera"><span className="flex items-center gap-2"><Database className="h-3 w-3"/> Iterra</span></SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center gap-3 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-sm font-medium">Loading storage matrix...</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8 items-start">
        {/* Data Portability (GDPR) */}
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col h-full">
          <div className="border-b px-6 py-5 bg-muted/5">
            <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2">
              <Shield className="h-5 w-5 text-emerald-500" />
              Data Portability
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Export a complete archive of your data for backup purposes.
            </p>
          </div>
          <div className="p-6 flex flex-col justify-between flex-1">
            <div className="flex flex-col gap-4">
              <Button
                variant="outline"
                onClick={handleExport}
                disabled={isExporting || !status?.connected}
                className="flex items-center gap-2 h-12 rounded-lg w-full justify-center border-border hover:bg-muted"
              >
                {isExporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Export Complete Archive (.zip)
              </Button>

              {!status?.connected && (
                <p className="text-xs text-amber-600/80 dark:text-amber-400/80 text-center font-medium bg-amber-50 dark:bg-amber-900/10 py-2 rounded-md">
                  Requires active Google Workspace connection.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Data Deletion */}
        <div className="rounded-xl border border-red-200 dark:border-red-900/50 bg-card shadow-sm overflow-hidden flex flex-col h-full group">
          <div className="border-b border-red-100 dark:border-red-900/30 px-6 py-5 bg-red-50/50 dark:bg-red-900/10">
            <h2 className="text-lg font-semibold tracking-tight flex items-center gap-2 text-red-600 dark:text-red-500">
              <Trash2 className="h-5 w-5" />
              Danger Zone
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Permanently purge all Iterra data from servers and Drive.
            </p>
          </div>
          <div className="p-6 flex flex-col justify-start flex-1">
            <Button
              variant="outline"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={isDeleting}
              className="flex items-center justify-center gap-2 h-12 w-full rounded-lg border-red-900/50 bg-red-950/30 text-red-500 hover:bg-red-950/50 hover:text-red-400 dark:border-red-900/30 dark:bg-red-950/20 dark:text-red-500 dark:hover:bg-red-900/40 dark:hover:text-red-400 transition-all shadow-sm mt-auto"
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Purge All User Data
            </Button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="border-red-200 dark:border-red-900/50 sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-red-600 dark:text-red-500 flex items-center gap-2">
              <Trash2 className="h-5 w-5" />
              Purge All Data?
            </DialogTitle>
            <DialogDescription className="pt-3">
              This will permanently delete:
              <ul className="mt-3 space-y-1.5 list-none">
                <li className="flex items-center gap-2 text-foreground"><CheckCircle className="h-4 w-4 text-red-500"/> All files in your Google Drive&apos;s Iterra folder</li>
                <li className="flex items-center gap-2 text-foreground"><CheckCircle className="h-4 w-4 text-red-500"/> All drafts stored on Iterra servers</li>
                <li className="flex items-center gap-2 text-foreground"><CheckCircle className="h-4 w-4 text-red-500"/> Your brand profile and analysis</li>
                <li className="flex items-center gap-2 text-foreground"><CheckCircle className="h-4 w-4 text-red-500"/> All scraped social media data</li>
              </ul>
              <Alert className="mt-4 border-red-200 bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-200 dark:border-red-900/50">
                <AlertDescription className="font-medium">
                  This action cannot be undone. Your account will remain but all data will be gone forever.
                </AlertDescription>
              </Alert>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-4">
            <Label className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
              Type <span className="text-red-600 dark:text-red-400 font-bold select-none">DELETE</span> to confirm
            </Label>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              className="flex h-11 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:border-red-500"
              placeholder="DELETE"
              autoComplete="off"
            />
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="ghost" onClick={() => setShowDeleteConfirm(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAll}
              disabled={deleteConfirmText !== "DELETE" || isDeleting}
              className="bg-red-600 hover:bg-red-700"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Purging...
                </>
              ) : (
                "Yes, Purge Everything"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </ProductShell>
  );
}
