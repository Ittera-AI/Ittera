"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import type { User as SupabaseUser } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";

export type User = { email: string; name: string; initials: string };
export type AuthMode = "signin" | "signup";

interface AuthContextType {
  user: User | null;
  sessionLoading: boolean;
  hasWorkspaceAccess: boolean;
  workspaceAccessLoading: boolean;
  workspaceAccessChecked: boolean;
  waitlistPosition: number | null;
  isAdmin: boolean;
  authOpen: boolean;
  authMode: AuthMode;
  authSeedEmail: string;
  openAuth: (mode?: AuthMode, seedEmail?: string) => void;
  closeAuth: () => void;
  setAuthMode: (mode: AuthMode) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<{ needsEmailConfirmation: boolean }>;
  signInWithGoogle: () => void;
  signInWithLinkedIn: () => void;
  resetPassword: (email: string) => Promise<void>;
  completeOAuthSignIn: (token: string) => Promise<void>;
  refreshWorkspaceAccess: () => Promise<boolean>;
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

function parseAdminEmails(): Set<string> {
  const raw = process.env.NEXT_PUBLIC_ADMIN_EMAILS ?? "";
  return new Set(
    raw
      .split(",")
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean),
  );
}

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
  const [hasWorkspaceAccess, setHasWorkspaceAccess] = useState(false);
  const [workspaceAccessLoading, setWorkspaceAccessLoading] = useState(false);
  const [workspaceAccessChecked, setWorkspaceAccessChecked] = useState(false);
  const [waitlistPosition, setWaitlistPosition] = useState<number | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [authSeedEmail, setAuthSeedEmail] = useState("");

  const isAdmin = user ? parseAdminEmails().has(user.email.toLowerCase()) : false;

  const refreshWorkspaceAccess = useCallback(async (): Promise<boolean> => {
    setWorkspaceAccessLoading(true);
    try {
      const status = await api.waitlist.myStatus();
      setHasWorkspaceAccess(status.access_approved);
      setWaitlistPosition(status.position);
      setWorkspaceAccessChecked(true);
      return status.access_approved;
    } catch {
      setHasWorkspaceAccess(false);
      setWaitlistPosition(null);
      setWorkspaceAccessChecked(true);
      return false;
    } finally {
      setWorkspaceAccessLoading(false);
    }
  }, []);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ? userFromSupabase(session.user) : null);
      setSessionLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? userFromSupabase(session.user) : null);
      if (session) {
        setAuthOpen(false);
        setAuthSeedEmail("");
      } else {
        setHasWorkspaceAccess(false);
        setWaitlistPosition(null);
        setWorkspaceAccessChecked(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!user) return;
    void refreshWorkspaceAccess();
  }, [user, refreshWorkspaceAccess]);

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
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim().toLowerCase(),
      password,
    });
    if (error) throw new Error(error.message);
    if (data.session?.user) {
      setUser(userFromSupabase(data.session.user));
    }
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
    if (data.session?.user) {
      setUser(userFromSupabase(data.session.user));
    }
    return { needsEmailConfirmation: !data.session };
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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const completeOAuthSignIn = useCallback(async (_token: string) => {}, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
    setHasWorkspaceAccess(false);
    setWaitlistPosition(null);
    setWorkspaceAccessChecked(false);
    setAuthOpen(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        sessionLoading,
        hasWorkspaceAccess,
        workspaceAccessLoading,
        workspaceAccessChecked,
        waitlistPosition,
        isAdmin,
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
        refreshWorkspaceAccess,
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
