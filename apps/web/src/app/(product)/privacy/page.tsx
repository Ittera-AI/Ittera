"use client";

/**
 * Privacy Dashboard Page
 *
 * Shows users where their data lives and provides privacy controls.
 */

import { useStorage } from "@/hooks/useStorage";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/Badge";
import {
  CheckCircle,
  Cloud,
  Database,
  FileText,
  Loader2,
  MapPin,
  Shield,
  XCircle,
} from "lucide-react";
import Link from "next/link";

export default function PrivacyDashboardPage() {
  const { dashboard, isLoading, error, refreshDashboard } = useStorage();

  const getLocationBadge = (location: string) => {
    switch (location) {
      case "google_drive":
        return (
          <Badge variant="default" className="gap-1">
            <Cloud className="h-3 w-3" />
            Google Drive
          </Badge>
        );
      case "iterra_db":
        return (
          <Badge variant="secondary" className="gap-1">
            <Database className="h-3 w-3" />
            Iterra Servers
          </Badge>
        );
      case "both":
        return (
          <Badge variant="outline" className="gap-1">
            <Cloud className="h-3 w-3" />
            Both Locations
          </Badge>
        );
      case "none":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            No Data
          </Badge>
        );
      default:
        return <Badge variant="outline">{location}</Badge>;
    }
  };

  return (
    <div className="container max-w-4xl py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Privacy Dashboard</h1>
        <p className="text-muted-foreground">
          See where your data is stored and manage your privacy settings.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : dashboard ? (
        <div className="space-y-6">
          {/* Overview Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Data Storage Overview
              </CardTitle>
              <CardDescription>
                Your data is stored in the following locations.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dashboard.data_locations.map((location) => (
                  <div
                    key={location.data_type}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 font-medium">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        {location.description}
                      </div>
                      {location.drive_file_id && (
                        <p className="text-xs text-muted-foreground">
                          Drive File ID: {location.drive_file_id.slice(0, 16)}...
                        </p>
                      )}
                    </div>
                    {getLocationBadge(location.storage_location)}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Connection Status */}
          <Card>
            <CardHeader>
              <CardTitle>Google Drive Connection</CardTitle>
              <CardDescription>
                Status of your Google Drive integration.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                {dashboard.drive_connected ? (
                  <>
                    <CheckCircle className="h-8 w-8 text-green-600" />
                    <div>
                      <p className="font-medium">Connected</p>
                      <p className="text-sm text-muted-foreground">
                        Folder ID: {dashboard.drive_folder_id?.slice(0, 16)}...
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <XCircle className="h-8 w-8 text-red-600" />
                    <div>
                      <p className="font-medium">Not Connected</p>
                      <p className="text-sm text-muted-foreground">
                        Connect Google Drive for privacy-first storage.
                      </p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Storage Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Your Storage Preferences</CardTitle>
              <CardDescription>
                How you&apos;ve configured data storage.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p>
                  <span className="font-medium">Default:</span>{" "}
                  {dashboard.storage_preferences?.default === "google_drive"
                    ? "Google Drive"
                    : dashboard.storage_preferences?.default === "local"
                    ? "Local Download"
                    : "Iterra Servers"}
                </p>
                {dashboard.data_retention_days !== null && (
                  <p>
                    <span className="font-medium">Data Retention:</span>{" "}
                    {dashboard.data_retention_days === 0
                      ? "Never delete"
                      : `${dashboard.data_retention_days} days`}
                  </p>
                )}
                {dashboard.next_cleanup_date && (
                  <p className="text-sm text-muted-foreground">
                    Next cleanup: {new Date(dashboard.next_cleanup_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              <div className="mt-4">
                <Link href="/settings/storage">
                  <Button variant="outline" size="sm">
                    Manage Storage Settings
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Pending Operations */}
          {dashboard.pending_operations > 0 && (
            <Card className="border-amber-200 bg-amber-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-amber-800">
                  <FileText className="h-5 w-5" />
                  Pending Operations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-amber-800">
                  You have {dashboard.pending_operations} operation(s) waiting to sync to Google Drive.
                  These will be processed automatically.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Data Rights */}
          <Card>
            <CardHeader>
              <CardTitle>Your Data Rights</CardTitle>
              <CardDescription>
                GDPR rights and controls for your data.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border p-4">
                  <h4 className="font-medium">Export Your Data (Article 20)</h4>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Download all your data in a portable format.
                  </p>
                  <Link href="/settings/storage">
                    <Button variant="outline" size="sm" className="mt-4">
                      Export Data
                    </Button>
                  </Link>
                </div>

                <div className="rounded-lg border p-4">
                  <h4 className="font-medium">Delete Your Data (Article 17)</h4>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Request deletion of all your personal data.
                  </p>
                  <Link href="/settings/storage">
                    <Button variant="destructive" size="sm" className="mt-4">
                      Delete All Data
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      <div className="mt-8 text-center">
        <Button variant="outline" onClick={refreshDashboard} disabled={isLoading}>
          {isLoading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Database className="mr-2 h-4 w-4" />
          )}
          Refresh Dashboard
        </Button>
      </div>
    </div>
  );
}
