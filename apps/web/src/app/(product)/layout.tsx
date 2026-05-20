"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

/** Auth gate for logged-in product routes (/dashboard, /create, …). Route group folder: `(product)`. */
export default function ProductRoutesLayout({ children }: { children: React.ReactNode }) {
  const { user, sessionLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!sessionLoading && !user) {
      router.replace("/");
    }
  }, [user, sessionLoading, router]);

  if (sessionLoading) {
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
          <p className="text-sm text-muted-foreground tracking-wide">Loading workspace…</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user) return null;

  return <>{children}</>;
}
