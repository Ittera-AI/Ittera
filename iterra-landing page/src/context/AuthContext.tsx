"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type User = { email: string; name: string; initials: string };
export type AuthMode = "signin" | "signup";

interface AuthContextType {
  user: User | null;
  authOpen: boolean;
  authMode: AuthMode;
  openAuth: (mode?: AuthMode) => void;
  closeAuth: () => void;
  setAuthMode: (mode: AuthMode) => void;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name: string) => Promise<void>;
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

  const openAuth = useCallback((mode: AuthMode = "signup") => {
    setAuthMode(mode);
    setAuthOpen(true);
  }, []);

  const closeAuth = useCallback(() => setAuthOpen(false), []);

  const signIn = useCallback(async (email: string, _password: string) => {
    await new Promise((r) => setTimeout(r, 1200));
    const raw = email.split("@")[0].replace(/[._-]/g, " ");
    const name = raw.replace(/\b\w/g, (c) => c.toUpperCase());
    setUser({ email, name, initials: makeInitials(name) });
    setAuthOpen(false);
  }, []);

  const signUp = useCallback(async (email: string, _password: string, name: string) => {
    await new Promise((r) => setTimeout(r, 1400));
    setUser({ email, name: name.trim(), initials: makeInitials(name) });
    setAuthOpen(false);
  }, []);

  const signOut = useCallback(() => setUser(null), []);

  return (
    <AuthContext.Provider
      value={{ user, authOpen, authMode, openAuth, closeAuth, setAuthMode, signIn, signUp, signOut }}
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
