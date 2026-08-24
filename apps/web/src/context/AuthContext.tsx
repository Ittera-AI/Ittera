"use client";

import { createContext, useContext, useState, useCallback, useEffect, useRef, ReactNode } from "react";
import type { Session, User as SupabaseUser } from "@supabase/supabase-js";
import { resetAuthBoundState } from "@/lib/auth-bound-state";
import { clearStoredSupabaseSessions, supabase } from "@/lib/supabase";
import { api } from "@/lib/api";

export type User = { id: string; email: string; name: string; initials: string };
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
  signOut: () => Promise<void>;
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
    id: supabaseUser.id,
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
  const principalIdRef = useRef<string | null>(null);
  const accessRequestGenerationRef = useRef(0);

  const isAdmin = user ? parseAdminEmails().has(user.email.toLowerCase()) : false;

  const clearWorkspaceAccessState = useCallback(() => {
    setHasWorkspaceAccess(false);
    setWaitlistPosition(null);
    setWorkspaceAccessChecked(false);
    setWorkspaceAccessLoading(false);
  }, []);

  const invalidateWorkspaceAccess = useCallback(() => {
    accessRequestGenerationRef.current += 1;
    clearWorkspaceAccessState();
  }, [clearWorkspaceAccessState]);

  const refreshWorkspaceAccess = useCallback(async (): Promise<boolean> => {
    const principalId = principalIdRef.current;
    const requestGeneration = ++accessRequestGenerationRef.current;

    setHasWorkspaceAccess(false);
    setWaitlistPosition(null);
    setWorkspaceAccessChecked(false);
    setWorkspaceAccessLoading(Boolean(principalId));

    if (!principalId) return false;

    const isCurrentRequest = () =>
      accessRequestGenerationRef.current === requestGeneration &&
      principalIdRef.current === principalId;

    try {
      const status = await api.waitlist.myStatus();
      if (!isCurrentRequest()) return false;

      setHasWorkspaceAccess(status.access_approved);
      setWaitlistPosition(status.position);
      setWorkspaceAccessChecked(true);
      return status.access_approved;
    } catch {
      if (!isCurrentRequest()) return false;

      setHasWorkspaceAccess(false);
      setWaitlistPosition(null);
      setWorkspaceAccessChecked(true);
      return false;
    } finally {
      if (isCurrentRequest()) setWorkspaceAccessLoading(false);
    }
  }, []);

  const applySession = useCallback(
    (session: Session | null) => {
      const previousPrincipalId = principalIdRef.current;
      const nextPrincipalId = session?.user.id ?? null;

      if (previousPrincipalId !== nextPrincipalId) {
        invalidateWorkspaceAccess();
        if (previousPrincipalId !== null) resetAuthBoundState("auth");
      }
      principalIdRef.current = nextPrincipalId;

      if (session?.user) {
        setUser(userFromSupabase(session.user));
        setAuthOpen(false);
        setAuthSeedEmail("");
      } else {
        setUser(null);
        clearWorkspaceAccessState();
      }
    },
    [clearWorkspaceAccessState, invalidateWorkspaceAccess],
  );

  const handleInvalidSession = useCallback(() => {
    principalIdRef.current = null;
    invalidateWorkspaceAccess();
    resetAuthBoundState("auth");
    setUser(null);
  }, [invalidateWorkspaceAccess]);

  useEffect(() => {
    // Purge legacy globally-persisted product/workspace data on first hydration.
    resetAuthBoundState("auth");
    window.addEventListener("ittera-auth-invalid", handleInvalidSession);

    supabase.auth
      .getSession()
      .then(({ data: { session } }) => {
        applySession(session);
      })
      .catch(() => {
        handleInvalidSession();
      })
      .finally(() => {
        setSessionLoading(false);
      });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      applySession(session);
    });

    return () => {
      accessRequestGenerationRef.current += 1;
      window.removeEventListener("ittera-auth-invalid", handleInvalidSession);
      subscription.unsubscribe();
    };
  }, [applySession, handleInvalidSession]);

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

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });
      if (error) throw new Error(error.message);
      if (data.session) applySession(data.session);
    },
    [applySession],
  );

  const signUp = useCallback(
    async (email: string, password: string, name: string) => {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: { full_name: name.trim(), name: name.trim() },
        },
      });
      if (error) throw new Error(error.message);
      if (data.session) applySession(data.session);
      return { needsEmailConfirmation: !data.session };
    },
    [applySession],
  );

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
    // Invalidate access synchronously so no in-flight request can re-authorize or
    // repopulate state while either logout transport is still pending.
    principalIdRef.current = null;
    invalidateWorkspaceAccess();
    resetAuthBoundState("auth");
    setUser(null);
    setAuthOpen(false);

    const [, supabaseResult] = await Promise.allSettled([
      api.auth.logout(),
      supabase.auth.signOut(),
    ]);
    if (
      supabaseResult.status === "rejected" ||
      (supabaseResult.status === "fulfilled" && supabaseResult.value.error)
    ) {
      clearStoredSupabaseSessions();
    }
  }, [invalidateWorkspaceAccess]);

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
