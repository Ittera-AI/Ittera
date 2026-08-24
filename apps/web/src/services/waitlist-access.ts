import {
  ApiError,
  api,
  type WaitlistMemberStatus,
  type WaitlistStats,
} from "@/lib/api";

export type WaitlistEnrollmentResult = {
  position: number | null;
  joined: boolean;
  alreadyJoined: boolean;
};

/** Ensure the normalized email has a waitlist row. The API operation is idempotent. */
export async function ensureWaitlistEntry(
  email: string,
  name?: string | null,
  profession?: string | null,
): Promise<WaitlistEnrollmentResult> {
  const normalizedEmail = email.trim().toLowerCase();
  if (!normalizedEmail.includes("@")) {
    throw new Error("Please enter a valid email address.");
  }

  const response = await api.waitlist.join({
    email: normalizedEmail,
    ...(name?.trim() ? { name: name.trim() } : {}),
    ...(profession?.trim() ? { profession: profession.trim() } : {}),
  });

  return {
    position: response.position,
    joined: true,
    alreadyJoined: response.already_joined,
  };
}

export type WaitlistFetchResult = {
  status: WaitlistMemberStatus | null;
  error: string | null;
};

export function fetchWaitlistStats(): Promise<WaitlistStats> {
  return api.waitlist.stats();
}

/** Fetch queue position for the signed-in user; failures remain explicit and fail closed. */
export async function fetchWaitlistMemberStatus(): Promise<WaitlistFetchResult> {
  try {
    const status = await api.waitlist.myStatus();
    return { status, error: null };
  } catch (error) {
    const message =
      error instanceof ApiError
        ? error.message
        : "Could not load your queue position. Is the API running?";
    return { status: null, error: message };
  }
}

export function emailsMatch(a: string | undefined, b: string | undefined) {
  if (!a || !b) return false;
  return a.trim().toLowerCase() === b.trim().toLowerCase();
}
