"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PenLine,
  CalendarDays,
  BarChart2,
  Radar,
  Zap,
  Settings,
  LogOut,
  Menu,
  X,
  ShieldCheck,
} from "lucide-react";
import { useState } from "react";
import type { User } from "@/context/AuthContext";
import { useAuth } from "@/context/AuthContext";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useProductStore } from "@/stores/product.store";

const NAV = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Create", href: "/create", icon: PenLine },
  { label: "Calendar", href: "/calendar", icon: CalendarDays },
  { label: "Analytics", href: "/analytics", icon: BarChart2 },
  { label: "Trend Radar", href: "/radar", icon: Radar },
  { label: "Coach", href: "/coach", icon: Zap },
] as const;

const BOTTOM_NAV = [{ label: "Settings", href: "/settings", icon: Settings }] as const;

function userInitials(user: User | null): string {
  if (!user) return "?";
  return user.name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => (w[0] ?? "").toUpperCase())
    .join("") || "?";
}

type ProductSidebarProps = {
  pathname: string;
  onNavigate: () => void;
  user: User | null;
  isAdmin?: boolean;
  onSignOut: () => void | Promise<void>;
};

function ProductSidebar({ pathname, onNavigate, user, isAdmin, onSignOut }: ProductSidebarProps) {
  const initials = userInitials(user);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-border/60 px-5 py-5">
        <Link href="/dashboard" className="group flex items-center gap-2" onClick={onNavigate}>
          <span
            className="flex h-6 w-6 items-center justify-center rounded-md text-xs font-bold text-white"
            style={{ background: "var(--bronze)" }}
          >
            It
          </span>
          <span className="text-base font-semibold tracking-[-0.03em] text-foreground">Ittera</span>
        </Link>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
          Workspace
        </p>
        {NAV.map(({ label, href, icon: Icon }, i) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              style={{
                animationDelay: `${i * 35}ms`,
                animationFillMode: "backwards",
              }}
              className={cn(
                "nav-item-shell flex animate-nav-in items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 active:scale-[0.97]",
                active
                  ? "bg-accent text-accent-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon size={16} className={cn(active ? "opacity-100" : "opacity-60")} strokeWidth={active ? 2.4 : 1.8} />
              {label}
              {active ? (
                <span className="ml-auto h-1.5 w-1.5 rounded-full" style={{ background: "var(--bronze)" }} />
              ) : null}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-0.5 border-t border-border/60 px-3 py-3">
        {BOTTOM_NAV.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 active:scale-[0.97]",
                active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon size={16} strokeWidth={1.8} className="opacity-60" />
              {label}
            </Link>
          );
        })}

        {isAdmin && (
          <Link
            href="/admin"
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 active:scale-[0.97]",
              pathname === "/admin" ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            <ShieldCheck size={16} strokeWidth={1.8} className="opacity-60" />
            Admin
          </Link>
        )}

        <div className="mt-2 flex items-center gap-3 rounded-lg px-3 py-2.5">
          <div
            className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
            style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}
          >
            {initials}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-foreground">{user?.name ?? "User"}</p>
            <p className="truncate text-[10px] text-muted-foreground">{user?.email ?? ""}</p>
          </div>
          <button
            title="Sign out"
            type="button"
            onClick={() => void onSignOut()}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-[0.97]"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

export function ProductShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, signOut, isAdmin } = useAuth() as any;
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeMobile = () => setMobileOpen(false);
  const productError = useProductStore((s) => s.error);
  const clearProductError = useProductStore((s) => s.clearError);

  return (
    <div className="flex min-h-screen bg-background">
      <aside
        className="fixed inset-y-0 left-0 z-30 hidden w-56 flex-shrink-0 flex-col lg:flex"
        style={{
          background: "var(--card)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <ProductSidebar pathname={pathname} onNavigate={() => {}} user={user} isAdmin={isAdmin} onSignOut={signOut} />
      </aside>

      {mobileOpen ? (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 lg:hidden"
          style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }}
          onClick={closeMobile}
        />
      ) : null}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-56 flex-col lg:hidden",
          "transition-transform duration-[220ms] cubic-bezier(0.32,0.72,0,1)",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
        style={{
          background: "var(--card)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <ProductSidebar pathname={pathname} onNavigate={closeMobile} user={user} isAdmin={isAdmin} onSignOut={signOut} />
      </aside>

      <div className="flex flex-1 flex-col lg:ml-56">
        <header
          className="sticky top-0 z-50 flex items-center gap-4 border-b border-border/60 px-4 py-3 lg:hidden"
          style={{
            background: "color-mix(in srgb, var(--card) 85%, transparent)",
            backdropFilter: "blur(16px) saturate(160%)",
            WebkitBackdropFilter: "blur(16px) saturate(160%)",
            boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)",
          }}
        >
          <button
            type="button"
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
            onClick={() => setMobileOpen((o) => !o)}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted active:scale-[0.97]"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <Link href="/dashboard" className="text-sm font-semibold tracking-[-0.03em]">
            Ittera
          </Link>
        </header>

        <main className="flex-1 overflow-x-hidden">
          <div className="mx-auto max-w-6xl px-4 py-8 md:px-8">
            {productError ? (
              <Alert variant="destructive" className="mb-6">
                <AlertTitle>Something went wrong</AlertTitle>
                <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
                  <span>{productError}</span>
                  <button
                    type="button"
                    onClick={() => clearProductError()}
                    className="shrink-0 rounded-md border border-border bg-background px-2 py-1 text-xs font-medium hover:bg-muted"
                  >
                    Dismiss
                  </button>
                </AlertDescription>
              </Alert>
            ) : null}
            {children}
          </div>
        </main>
      </div>

      <style>{`
        @keyframes navIn {
          from { opacity: 0; transform: translateX(-6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        .animate-nav-in { animation: navIn 220ms cubic-bezier(0.23,1,0.32,1) both; }
      `}</style>
    </div>
  );
}
