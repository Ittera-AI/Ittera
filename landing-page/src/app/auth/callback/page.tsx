"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useAuth } from "@/context/AuthContext";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { completeOAuthSignIn } = useAuth();
  const [message, setMessage] = useState("Completing Google sign-in...");

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      setMessage(error);
      return;
    }

    if (!token) {
      setMessage("Missing OAuth token.");
      return;
    }

    let cancelled = false;

    completeOAuthSignIn(token)
      .then(() => {
        if (!cancelled) router.replace("/");
      })
      .catch((err) => {
        if (!cancelled) {
          setMessage(err instanceof Error ? err.message : "Unable to complete Google sign-in.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [completeOAuthSignIn, router, searchParams]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6 bg-[#F9F8F6] text-[#171717]">
      <div className="max-w-md text-center">
        <h1 className="text-2xl font-semibold tracking-tight mb-3">Google Sign-In</h1>
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
            <h1 className="text-2xl font-semibold tracking-tight mb-3">Google Sign-In</h1>
            <p className="text-sm text-[#525252]">Completing Google sign-in...</p>
          </div>
        </main>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
