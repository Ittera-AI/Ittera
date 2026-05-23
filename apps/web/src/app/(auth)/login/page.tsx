"use client";

import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";

import { useAuth } from "@/hooks/useAuth";
import { redirectAfterSignIn } from "@/lib/routes";

function LoginForm() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await signIn(email, password);
      redirectAfterSignIn();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-16">
      <section className="w-full max-w-md rounded-lg border border-[#EAEAEC] bg-white p-8 shadow-sm">
        <p className="eyebrow">Ittera</p>
        <h1 className="mt-3 text-3xl font-semibold text-[#171717]">Welcome back</h1>
        <p className="mt-2 text-sm text-neutral-600">Sign in to plan, analyze, and improve your content loop.</p>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-neutral-800">
            Email
            <input
              className="mt-2 w-full rounded-md border border-[#EAEAEC] px-3 py-2 outline-none focus:border-[#A38A70]"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              required
            />
          </label>

          <label className="block text-sm font-medium text-neutral-800">
            Password
            <input
              className="mt-2 w-full rounded-md border border-[#EAEAEC] px-3 py-2 outline-none focus:border-[#A38A70]"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
              required
            />
          </label>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <button
            className="w-full rounded-md bg-[#171717] px-4 py-3 text-sm font-semibold text-white transition hover:bg-black disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-sm text-neutral-600">
          New here? Join the waitlist from the <Link className="font-medium text-[#8B6F52]" href="/">home page</Link>.
        </p>
      </section>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="min-h-screen" />}>
      <LoginForm />
    </Suspense>
  );
}
