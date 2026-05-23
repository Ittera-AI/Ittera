import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? "";

const PLACEHOLDER_MARKERS = [
  "placeholder.supabase.co",
  "your-project-ref.supabase.co",
  "your-anon-public-key",
  "placeholder-anon-key",
];

function isPlaceholderValue(value: string) {
  return PLACEHOLDER_MARKERS.some((marker) => value.includes(marker));
}

export const isSupabaseConfigured =
  Boolean(supabaseUrl && supabaseAnonKey) &&
  !isPlaceholderValue(supabaseUrl) &&
  !isPlaceholderValue(supabaseAnonKey);

if (!isSupabaseConfigured && typeof window !== "undefined") {
  console.warn(
    "Supabase is not configured. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to apps/web/.env.local, then restart the dev server.",
  );
}

/** Avoid fake hostnames that trigger browser DNS errors when env is missing. */
const resolvedUrl = isSupabaseConfigured ? supabaseUrl : "http://127.0.0.1:54321";
const resolvedKey = isSupabaseConfigured ? supabaseAnonKey : "supabase-not-configured";

export const supabase = createClient(resolvedUrl, resolvedKey);

/** Fast local check — avoids flashing marketing pages while Supabase restores session. */
export function hasStoredSupabaseSession(): boolean {
  if (typeof window === "undefined") return false;

  try {
    for (let i = 0; i < localStorage.length; i += 1) {
      const key = localStorage.key(i);
      if (!key?.startsWith("sb-") || !key.endsWith("-auth-token")) continue;
      const raw = localStorage.getItem(key);
      if (raw && raw !== "null") return true;
    }
  } catch {
    // localStorage may be blocked
  }

  return false;
}
