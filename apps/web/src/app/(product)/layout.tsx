"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { supabase } from "@/lib/supabase";

/** Auth gate for logged-in product routes (/dashboard, /create, …). Route group folder: `(product)`. */
export default function ProductRoutesLayout({ children }: { children: React.ReactNode }) {
  const { user, sessionLoading } = useAuth();
  const router = useRouter();
  const [sessionProbe, setSessionProbe] = useState<"idle" | "has-session" | "no-session">("idle");

  useEffect(() => {
    if (sessionLoading || user) {
      return;
    }

    let cancelled = false;

    supabase.auth
      .getSession()
      .then(({ data: { session } }) => {
        if (cancelled) return;
        setSessionProbe(session ? "has-session" : "no-session");
        if (!session) {
          router.replace("/");
        }
      })
      .catch(() => {
        if (cancelled) return;
        setSessionProbe("no-session");
        router.replace("/");
      });

    return () => {
      cancelled = true;
    };
  }, [user, sessionLoading, router]);

  const sessionChecked = sessionLoading || Boolean(user) || sessionProbe !== "idle";
  const hasSupabaseSession = Boolean(user) || sessionProbe === "has-session";
  const waitingForUser = hasSupabaseSession && !user;

  if (sessionLoading || !sessionChecked || waitingForUser) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div
            className="h-8 w-8 rounded-full border-2 border-transparent"
            style={{
              borderTopColor: "var(--bronze)",
              animation: "spin 0.7s linear infinite",
            }}
          />
          <p className="text-sm text-muted-foreground tracking-wide">
            {sessionLoading ? "Loading workspace…" : "Checking session…"}
          </p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}
