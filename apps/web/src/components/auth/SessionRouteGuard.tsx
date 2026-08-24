"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { hasStoredSupabaseSession } from "@/lib/supabase";
import { MARKETING_PATHS, ROUTES, waitlistDestination } from "@/lib/routes";
import AuthTransitionScreen from "@/components/auth/AuthTransitionScreen";

/** Keep signed-in users off marketing pages — send them to waitlist status or dashboard. */
export default function SessionRouteGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const {
    user,
    hasWorkspaceAccess,
    sessionLoading,
    workspaceAccessChecked,
    workspaceAccessLoading,
  } = useAuth();

  // Defer session-presence check to a client-side effect to avoid hydration mismatch.
  // On the server, localStorage isn't available so hasStoredSupabaseSession() would
  // return false, but on the client it returns true — causing a React hydration error.
  const [mounted, setMounted] = useState(false);
  const [likelySession, setLikelySession] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setMounted(true);
      setLikelySession(hasStoredSupabaseSession());
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  const isMarketingRoute = MARKETING_PATHS.some(
    (path) => pathname === path || (path !== "/" && pathname.startsWith(`${path}/`)),
  );

  // Only hide marketing pages after the client has mounted and confirmed a session exists.
  const hideMarketing =
    mounted && isMarketingRoute && (Boolean(user) || (sessionLoading && likelySession));

  useEffect(() => {
    if (pathname !== ROUTES.home || searchParams.get("access") !== "pending") return;

    if (user) {
      router.replace(ROUTES.waitlistStatus);
      return;
    }

    router.replace(ROUTES.home);
    requestAnimationFrame(() => {
      document.getElementById("waitlist")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [pathname, searchParams, router, user]);

  useEffect(() => {
    if (
      !isMarketingRoute ||
      !user ||
      workspaceAccessLoading ||
      !workspaceAccessChecked
    ) {
      return;
    }
    router.replace(waitlistDestination(hasWorkspaceAccess));
  }, [
    hasWorkspaceAccess,
    isMarketingRoute,
    router,
    user,
    workspaceAccessChecked,
    workspaceAccessLoading,
  ]);

  if (hideMarketing) {
    return <AuthTransitionScreen />;
  }

  return <>{children}</>;
}
