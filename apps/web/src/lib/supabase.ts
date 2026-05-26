import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

/** True when a Supabase session token is present in browser storage (before client hydrates). */
export function hasStoredSupabaseSession(): boolean {
  if (typeof window === "undefined") return false;

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith("sb-") || !key.endsWith("-auth-token")) continue;

      const raw = localStorage.getItem(key);
      if (!raw) continue;

      const parsed = JSON.parse(raw) as { access_token?: string };
      if (parsed.access_token) return true;
    }
  } catch {
    return false;
  }

  return false;
}
