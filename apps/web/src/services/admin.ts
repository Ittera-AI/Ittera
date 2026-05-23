import { apiFetch } from "./api";

export type AdminWaitlistEntry = {
  email: string;
  name: string | null;
  profession: string | null;
  access_approved: boolean;
  approved_at: string | null;
  approved_by: string | null;
  created_at: string;
};

export async function fetchAdminWaitlistEntries(): Promise<AdminWaitlistEntry[]> {
  const data = await apiFetch<{ entries: AdminWaitlistEntry[] }>("/api/v1/waitlist/admin/entries");
  return data.entries;
}

export async function approveWaitlistUser(email: string): Promise<void> {
  await apiFetch("/api/v1/waitlist/admin/approve", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export async function revokeWaitlistUser(email: string): Promise<void> {
  await apiFetch("/api/v1/waitlist/admin/revoke", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}
