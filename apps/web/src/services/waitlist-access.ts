import { ApiError, apiFetch } from "@/services/api";

export type WaitlistEnrollmentResult = {
  position: number | null;
  joined: boolean;
};

type WaitlistJoinResponse = {
  position: number;
  already_joined: boolean;
};

/** Ensure the signed-in email has a waitlist row (idempotent). */
export async function ensureWaitlistEntry(
  email: string,
  name?: string | null,
): Promise<WaitlistEnrollmentResult> {
  const normalizedEmail = email.trim().toLowerCase();
  if (!normalizedEmail.includes("@")) {
    return { position: null, joined: false };
  }

  try {
    const response = await apiFetch<WaitlistJoinResponse>("/api/v1/waitlist", {
      method: "POST",
      body: JSON.stringify({
        email: normalizedEmail,
        name: name?.trim() || null,
      }),
    });
    return { position: response.position, joined: true };
  } catch {
    // Waitlist enrollment is best-effort; auth should still succeed.
    return { position: null, joined: false };
  }
}

export type WaitlistMemberStatus = {
  email: string;
  joined: boolean;
  access_approved: boolean;
  approved_at: string | null;
  position: number | null;
  total_joined: number;
  total_seats: number;
  remaining_seats: number;
};

export type WaitlistFetchResult = {
  status: WaitlistMemberStatus | null;
  error: string | null;
};

/** Fetch queue position for the signed-in user. */
export async function fetchWaitlistMemberStatus(): Promise<WaitlistFetchResult> {
  try {
    const status = await apiFetch<WaitlistMemberStatus>("/api/v1/waitlist/me");
    return { status, error: null };
  } catch (err) {
    const message =
      err instanceof ApiError
        ? err.message
        : "Could not load your queue position. Is the API running?";
    return { status: null, error: message };
  }
}

export function emailsMatch(a: string | undefined, b: string | undefined) {
  if (!a || !b) return false;
  return a.trim().toLowerCase() === b.trim().toLowerCase();
}
