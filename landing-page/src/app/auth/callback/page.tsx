"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Derive URL-level errors directly — no synchronous setState in effect.
  const urlError = searchParams.get("error");
  const urlErrorDesc = searchParams.get("error_description");
  const code = searchParams.get("code");

  const [asyncError, setAsyncError] = useState<string | null>(null);

  // Displayed message: URL error takes priority, then async error, then default.
  const message = urlError
    ? (urlErrorDesc ?? urlError)
    : asyncError ?? "Completing sign-in…";

  useEffect(() => {
    // URL already carries the error — nothing async to do.
    if (urlError) return;

    // No code and no error means direct visit — send home.
    if (!code) {
      router.replace("/");
      return;
    }

    let cancelled = false;

    supabase.auth
      .exchangeCodeForSession(code)
      .then(({ error: sessionError }) => {
        if (cancelled) return;
        if (sessionError) {
          setAsyncError(sessionError.message);
          return;
        }
        router.replace("/");
      });

    return () => {
      cancelled = true;
    };
  }, [router, code, urlError]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6 bg-[#F9F8F6] text-[#171717]">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-semibold tracking-tight mb-3">Signing in…</h1>
        <p className="text-sm text-[#525252]">{message}</p>
      </div>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center px-6 bg-[#F9F8F6] text-[#171717]">
          <div className="max-w-md text-center">
            <h1 className="text-2xl font-semibold tracking-tight mb-3">Signing in…</h1>
            <p className="text-sm text-[#525252]">Completing sign-in…</p>
          </div>
        </main>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
