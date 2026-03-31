"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import type { User as SupabaseUser } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

export type User = { email: string; name: string; initials: string };
export type AuthMode = "signin" | "signup";

interface AuthContextType {
  user: User | null;
  sessionLoading: boolean;
  authOpen: boolean;
  authMode: AuthMode;
  authSeedEmail: string;
  openAuth: (mode?: AuthMode, seedEmail?: string) => void;
  closeAuth: () => void;
  setAuthMode: (mode: AuthMode) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signInWithGoogle: () => void;
  signInWithLinkedIn: () => void;
  resetPassword: (email: string) => Promise<void>;
  // Kept for interface compatibility — no longer used directly
  completeOAuthSignIn: (token: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function makeInitials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function userFromSupabase(supabaseUser: SupabaseUser): User {
  const name =
    (supabaseUser.user_metadata?.full_name as string | undefined) ||
    (supabaseUser.user_metadata?.name as string | undefined) ||
    supabaseUser.email?.split("@")[0] ||
    "User";
  return {
    email: supabaseUser.email ?? "",
    name,
    initials: makeInitials(name),
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [authSeedEmail, setAuthSeedEmail] = useState("");

  useEffect(() => {
    // Restore session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ? userFromSupabase(session.user) : null);
      setSessionLoading(false);
    });

    // Listen for sign-in / sign-out / token refresh
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? userFromSupabase(session.user) : null);
      if (session) {
        setAuthOpen(false);
        setAuthSeedEmail("");
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const openAuth = useCallback((mode: AuthMode = "signup", seedEmail = "") => {
    setAuthMode(mode);
    setAuthSeedEmail(seedEmail.trim().toLowerCase());
    setAuthOpen(true);
  }, []);

  const closeAuth = useCallback(() => {
    setAuthOpen(false);
    setAuthSeedEmail("");
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email: email.trim().toLowerCase(),
      password,
    });
    if (error) throw new Error(error.message);
  }, []);

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    const { data, error } = await supabase.auth.signUp({
      email: email.trim().toLowerCase(),
      password,
      options: {
        data: { full_name: name.trim(), name: name.trim() },
      },
    });
    if (error) throw new Error(error.message);
    // If no session was returned, Supabase requires email confirmation first
    if (!data.session) {
      throw new Error(
        "Account created! Check your inbox and confirm your email before signing in.",
      );
    }
    // Session returned means email confirmation is off — onAuthStateChange handles login
  }, []);

  const signInWithGoogle = useCallback(() => {
    supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  }, []);

  const signInWithLinkedIn = useCallback(() => {
    supabase.auth.signInWithOAuth({
      provider: "linkedin_oidc",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
  }, []);

  const resetPassword = useCallback(async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(
      email.trim().toLowerCase(),
      { redirectTo: `${window.location.origin}/auth/callback` },
    );
    if (error) throw new Error(error.message);
  }, []);

  // No-op kept for backwards interface compatibility
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const completeOAuthSignIn = useCallback(async (_token: string) => {}, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
    setAuthOpen(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        sessionLoading,
        authOpen,
        authMode,
        authSeedEmail,
        openAuth,
        closeAuth,
        setAuthMode,
        signIn,
        signUp,
        signInWithGoogle,
        signInWithLinkedIn,
        resetPassword,
        completeOAuthSignIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
