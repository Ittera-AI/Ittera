"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";

export type User = { email: string; name: string; initials: string };
export type AuthMode = "signin" | "signup";

interface AuthContextType {
  user: User | null;
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [authSeedEmail, setAuthSeedEmail] = useState("");

  const openAuth = useCallback((mode: AuthMode = "signup", seedEmail = "") => {
    setAuthMode(mode);
    setAuthSeedEmail(seedEmail.trim().toLowerCase());
    setAuthOpen(true);
  }, []);

  const closeAuth = useCallback(() => {
    setAuthOpen(false);
    setAuthSeedEmail("");
  }, []);

  const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  const fetchCurrentUser = useCallback(async (token: string) => {
    const res = await fetch(`${API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? "Unable to restore your session");
    }

    const data = await res.json();
    return {
      email: data.email,
      name: data.name,
      initials: makeInitials(data.name),
    } satisfies User;
  }, [API]);

  useEffect(() => {
    const token = localStorage.getItem("ittera_token");
    if (!token) return;

    let cancelled = false;

    fetchCurrentUser(token)
      .then((currentUser) => {
        if (!cancelled) setUser(currentUser);
      })
      .catch(() => {
        localStorage.removeItem("ittera_token");
        if (!cancelled) setUser(null);
      });

    return () => {
      cancelled = true;
    };
  }, [fetchCurrentUser]);

  const completeOAuthSignIn = useCallback(async (token: string) => {
    localStorage.setItem("ittera_token", token);
    const currentUser = await fetchCurrentUser(token);
    setUser(currentUser);
    setAuthSeedEmail("");
    setAuthOpen(false);
  }, [fetchCurrentUser]);

  const signIn = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? "Invalid email or password");
    }
    const { access_token } = await res.json();
    await completeOAuthSignIn(access_token);
  }, [API, completeOAuthSignIn]);

  const signUp = useCallback(async (email: string, password: string, name: string) => {
    const res = await fetch(`${API}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.trim().toLowerCase(), password, name: name.trim() }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail ?? "Registration failed");
    }
    // Auto sign in after register
    await signIn(email, password);
  }, [API, signIn]);

  const signInWithGoogle = useCallback(() => {
    window.location.href = `${API}/api/v1/auth/google/start`;
  }, [API]);

  const signInWithLinkedIn = useCallback(() => {
    window.location.href = `${API}/api/v1/auth/linkedin/start`;
  }, [API]);

  const signOut = useCallback(() => {
    localStorage.removeItem("ittera_token");
    setUser(null);
    setAuthOpen(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
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
