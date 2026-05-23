"use client";

import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

/** Minimal shell shown while resolving session or redirecting signed-in users off marketing pages. */
export default function AuthTransitionScreen() {
  return (
    <main className="fixed inset-0 z-50 flex items-center justify-center bg-background px-6">
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
        <p className="text-sm font-medium text-muted-foreground">Authenticating your session...</p>
      </motion.div>
    </main>
  );
}
