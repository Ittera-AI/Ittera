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
  const { user, hasWorkspaceAccess, sessionLoading } = useAuth();
  const [likelySession] = useState(() => hasStoredSupabaseSession());

  const isMarketingRoute = MARKETING_PATHS.some(
    (path) => pathname === path || (path !== "/" && pathname.startsWith(`${path}/`)),
  );

  const hideMarketing =
    isMarketingRoute && (Boolean(user) || (sessionLoading && likelySession));

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
    if (!isMarketingRoute || !user) return;
    // Always route to dashboard and let its layout check workspace access properly
    router.replace(ROUTES.dashboard);
  }, [isMarketingRoute, user, router]);

  if (hideMarketing) {
    return <AuthTransitionScreen />;
  }

  return <>{children}</>;
}
