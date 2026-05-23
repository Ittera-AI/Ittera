"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabase";
import { ROUTES } from "@/lib/routes";
/** Auth gate for logged-in product routes (/dashboard, /create, …). Route group folder: `(product)`. */
export default function ProductRoutesLayout({ children }: { children: React.ReactNode }) {
  const { user, sessionLoading, hasWorkspaceAccess, refreshWorkspaceAccess, workspaceAccessLoading } = useAuth();
  const router = useRouter();
  const [sessionState, setSessionState] = useState<"checking" | "valid" | "invalid">("checking");

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      if (sessionLoading || workspaceAccessLoading) {
        return;
      }

      if (user) {
        const allowed = hasWorkspaceAccess || (await refreshWorkspaceAccess());
        if (allowed) {
          if (!user.onboarding_complete && (typeof sessionStorage === "undefined" || sessionStorage.getItem("skipped_onboarding") !== "true")) {
            if (!cancelled) router.replace("/onboarding/persona");
            return;
          }
          if (!cancelled) setSessionState("valid");
          return;
        }
        if (!cancelled) setSessionState("invalid");
        router.replace(ROUTES.waitlistStatus);
        return;
      }

      setSessionState("checking");

      const { data: { session } } = await supabase.auth.getSession();
      if (cancelled) return;

      if (session) {
        setSessionState("checking");
        return;
      }

      setSessionState("invalid");
      router.replace(ROUTES.home);
    }

    void checkSession();

    return () => {
      cancelled = true;
    };
  }, [user, sessionLoading, workspaceAccessLoading, hasWorkspaceAccess, refreshWorkspaceAccess, router]);

  if (sessionLoading || workspaceAccessLoading || sessionState === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="flex max-w-sm flex-col items-center text-center animate-in fade-in zoom-in duration-500">
          <div className="relative mb-6 flex h-16 w-16 items-center justify-center">
            <div className="absolute inset-0 animate-ping rounded-full bg-[var(--bronze)]/20" />
            <div className="relative flex h-full w-full items-center justify-center rounded-full bg-[var(--bronze)]/10 text-[var(--bronze)]">
              <svg
                className="h-7 w-7 animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
            </div>
          </div>
          <h1 className="mb-2 text-2xl font-bold tracking-tight text-foreground">Preparing Workspace</h1>
          <p className="text-sm font-medium text-muted-foreground">
            {sessionLoading ? "Loading your profile..." : "Checking access permissions..."}
          </p>
        </div>
      </div>
    );
  }

  if (sessionState !== "valid" || !user) return null;

  return <>{children}</>;
}
