"use client";

import { createContext, useContext, useState, useCallback, useEffect, useRef, type ReactNode } from "react";
import type { User as SupabaseUser } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";
import { apiFetch } from "@/services/api";
import {
  emailsMatch,
  ensureWaitlistEntry,
  fetchWaitlistMemberStatus,
} from "@/services/waitlist-access";

export type User = { email: string; name: string; initials: string; onboarding_complete?: boolean };
export type AuthMode = "signin" | "signup";

export type WorkspaceAccessState = {
  email: string;
  has_access: boolean;
  waitlisted?: boolean;
  access_approved?: boolean;
  approved_at?: string | null;
  reason?: "pending_approval" | "not_waitlisted" | null;
  is_admin?: boolean;
};

interface AuthContextType {
  user: User | null;
  sessionLoading: boolean;
  workspaceAccessLoading: boolean;
  workspaceAccessChecked: boolean;
  hasWorkspaceAccess: boolean;
  isAdmin: boolean;
  isWaitlistedUser: boolean;
  waitlistPosition: number | null;
  refreshWorkspaceAccess: () => Promise<boolean>;
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
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

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
    onboarding_complete: supabaseUser.user_metadata?.onboarding_complete,
  };
}

function pendingAccess(email: string): WorkspaceAccessState {
  return { email, has_access: false, waitlisted: true, reason: "pending_approval" };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [workspaceAccess, setWorkspaceAccess] = useState<WorkspaceAccessState | null>(null);
  const [workspaceAccessLoading, setWorkspaceAccessLoading] = useState(false);
  const [waitlistPosition, setWaitlistPosition] = useState<number | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [authSeedEmail, setAuthSeedEmail] = useState("");
  const syncGenerationRef = useRef(0);

  const refreshWorkspaceAccess = useCallback(async (): Promise<boolean> => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user?.email) {
      setWorkspaceAccess(null);
      setWaitlistPosition(null);
      return false;
    }

    const email = session.user.email;
    const displayName =
      (session.user.user_metadata?.full_name as string | undefined) ||
      (session.user.user_metadata?.name as string | undefined) ||
      email.split("@")[0];

    const generation = ++syncGenerationRef.current;
    setWorkspaceAccessLoading(true);

    const syncPosition = async () => {
      const { status } = await fetchWaitlistMemberStatus();
      if (generation !== syncGenerationRef.current) return status?.position ?? null;
      if (status?.position != null) {
        setWaitlistPosition(status.position);
      }
      return status?.position ?? null;
    };

    try {
      const enrollment = await ensureWaitlistEntry(email, displayName);
      if (generation === syncGenerationRef.current && enrollment.position != null) {
        setWaitlistPosition(enrollment.position);
      }

      let access: WorkspaceAccessState;
      try {
        access = await apiFetch<WorkspaceAccessState>("/api/v1/auth/workspace-access");
      } catch {
        if (generation === syncGenerationRef.current) {
          setWorkspaceAccess(pendingAccess(email));
        }
        if (enrollment.position == null) {
          await syncPosition();
        }
        return false;
      }

      if (generation !== syncGenerationRef.current) return access.has_access;

      setWorkspaceAccess(access);

      if (access.has_access) {
        setWaitlistPosition(null);
        return true;
      }

      if (enrollment.position == null) {
        await syncPosition();
      }

      return false;
    } catch {
      if (generation !== syncGenerationRef.current) return false;
      setWorkspaceAccess(pendingAccess(email));
      await syncPosition();
      return false;
    } finally {
      if (generation === syncGenerationRef.current) {
        setWorkspaceAccessLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    let sessionReady = false;

    const finishInitialLoad = () => {
      if (sessionReady) return;
      sessionReady = true;
      setSessionLoading(false);
    };

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? userFromSupabase(session.user) : null);
      finishInitialLoad();
      if (session) {
        setAuthOpen(false);
        setAuthSeedEmail("");
      } else {
        syncGenerationRef.current += 1;
        setWorkspaceAccess(null);
        setWaitlistPosition(null);
        setWorkspaceAccessLoading(false);
      }
    });

    const fallbackTimer = window.setTimeout(finishInitialLoad, 2_000);

    return () => {
      subscription.unsubscribe();
      window.clearTimeout(fallbackTimer);
    };
  }, []);

  useEffect(() => {
    if (!user?.email) {
      syncGenerationRef.current += 1;
      setWorkspaceAccess(null);
      setWaitlistPosition(null);
      setWorkspaceAccessLoading(false);
      return;
    }

    setWorkspaceAccess((prev) =>
      prev && emailsMatch(prev.email, user.email) ? prev : pendingAccess(user.email),
    );

    void refreshWorkspaceAccess();
  }, [user?.email, refreshWorkspaceAccess]);

  const hasWorkspaceAccess = Boolean(
    user &&
      workspaceAccess &&
      emailsMatch(workspaceAccess.email, user.email) &&
      workspaceAccess.has_access,
  );

  const workspaceAccessChecked = Boolean(
    user &&
      workspaceAccess &&
      emailsMatch(workspaceAccess.email, user.email),
  );

  const isWaitlistedUser = Boolean(user && workspaceAccessChecked && !hasWorkspaceAccess);

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
      const nextUser = userFromSupabase(data.session.user);
      setUser(nextUser);
      setWorkspaceAccess(pendingAccess(nextUser.email));
      setSessionLoading(false);
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
      const nextUser = userFromSupabase(data.session.user);
      setUser(nextUser);
      setWorkspaceAccess(pendingAccess(nextUser.email));
      setSessionLoading(false);
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
    syncGenerationRef.current += 1;
    setUser(null);
    setWorkspaceAccess(null);
    setWaitlistPosition(null);
    setWorkspaceAccessLoading(false);
  }, []);

  const value: AuthContextType = {
    user,
    sessionLoading,
    workspaceAccessLoading,
    workspaceAccessChecked: workspaceAccess !== null,
    hasWorkspaceAccess: !!workspaceAccess?.has_access,
    isAdmin: !!workspaceAccess?.is_admin,
    isWaitlistedUser: !!workspaceAccess?.waitlisted,
    waitlistPosition,
    refreshWorkspaceAccess,
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
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
