"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { redirectAfterSignIn } from "@/lib/routes";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const urlError = searchParams.get("error");
  const urlErrorDesc = searchParams.get("error_description");
  const code = searchParams.get("code");

  const [asyncError, setAsyncError] = useState<string | null>(null);

  const message = urlError
    ? (urlErrorDesc ?? urlError)
    : asyncError ?? "Verifying your credentials...";

  useEffect(() => {
    if (urlError) return;
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
        // Redirecting straight to dashboard avoids a flash of marketing pages
        redirectAfterSignIn();
      });

    return () => {
      cancelled = true;
    };
  }, [router, code, urlError]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="flex max-w-sm flex-col items-center text-center"
      >
        <div className="relative mb-6 flex h-16 w-16 items-center justify-center">
          <div className="absolute inset-0 animate-ping rounded-full bg-[var(--bronze)]/20" />
          <div className="relative flex h-full w-full items-center justify-center rounded-full bg-[var(--bronze)]/10 text-[var(--bronze)]">
            <Loader2 className="h-7 w-7 animate-spin" />
          </div>
        </div>
        <h1 className="mb-2 text-2xl font-bold tracking-tight text-foreground">Secure Login</h1>
        <p className="text-sm font-medium text-muted-foreground">{message}</p>
      </motion.div>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="flex min-h-screen items-center justify-center bg-background px-6">
          <div className="flex max-w-sm flex-col items-center text-center">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[var(--bronze)]/10 text-[var(--bronze)]">
              <Loader2 className="h-7 w-7 animate-spin" />
            </div>
            <h1 className="mb-2 text-2xl font-bold tracking-tight text-foreground">Secure Login</h1>
            <p className="text-sm font-medium text-muted-foreground">Verifying your credentials...</p>
          </div>
        </main>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
