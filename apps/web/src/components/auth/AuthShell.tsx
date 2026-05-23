"use client";

import { Suspense, type ReactNode } from "react";
import SessionRouteGuard from "@/components/auth/SessionRouteGuard";

export default function AuthShell({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={null}>
      <SessionRouteGuard>{children}</SessionRouteGuard>
    </Suspense>
  );
}
