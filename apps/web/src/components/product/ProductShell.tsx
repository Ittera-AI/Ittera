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
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { useState, useEffect } from "react";
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
  onSignOut: () => void | Promise<void>;
  isCollapsed: boolean;
  onToggleCollapse?: () => void;
};

function ProductSidebar({ pathname, onNavigate, user, onSignOut, isCollapsed, onToggleCollapse }: ProductSidebarProps) {
  const initials = userInitials(user);

  return (
    <div className="flex h-full flex-col">
      <div className={cn("flex items-center border-b border-border/60 px-4 py-4 h-[68px]", isCollapsed ? "justify-center" : "justify-between")}>
        <Link href="/dashboard" className="group flex items-center gap-2" onClick={onNavigate} title={isCollapsed ? "Ittera" : undefined}>
          <span
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white shadow-sm"
            style={{ background: "var(--bronze)" }}
          >
            It
          </span>
          {!isCollapsed && <span className="text-base font-semibold tracking-[-0.03em] text-foreground">Ittera</span>}
        </Link>
        {!isCollapsed && onToggleCollapse && (
          <button
            type="button"
            onClick={onToggleCollapse}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors active:scale-95"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose size={16} />
          </button>
        )}
      </div>

      {isCollapsed && onToggleCollapse && (
        <div className="flex justify-center pt-4 pb-2">
          <button
            type="button"
            onClick={onToggleCollapse}
            className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors active:scale-95 shadow-sm border border-transparent hover:border-border/60 bg-background/50"
            aria-label="Expand sidebar"
            title="Expand sidebar"
          >
            <PanelLeftOpen size={16} />
          </button>
        </div>
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5 overflow-x-hidden">
        {!isCollapsed && (
          <p className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 whitespace-nowrap">
            Workspace
          </p>
        )}
        {NAV.map(({ label, href, icon: Icon }, i) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              title={isCollapsed ? label : undefined}
              style={{
                animationDelay: `${i * 35}ms`,
                animationFillMode: "backwards",
              }}
              className={cn(
                "nav-item-shell flex animate-nav-in items-center rounded-xl text-sm font-medium transition-all duration-200 active:scale-[0.97] whitespace-nowrap",
                isCollapsed ? "justify-center p-3" : "gap-3 px-3 py-2.5",
                active
                  ? "bg-primary/10 text-primary shadow-sm"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon size={isCollapsed ? 18 : 16} className={cn(active ? "opacity-100" : "opacity-70", "shrink-0")} strokeWidth={active ? 2.2 : 1.8} />
              {!isCollapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-1 border-t border-border/60 px-3 py-3 overflow-x-hidden">
        {BOTTOM_NAV.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              title={isCollapsed ? label : undefined}
              className={cn(
                "flex items-center rounded-xl text-sm font-medium transition-all duration-200 active:scale-[0.97] whitespace-nowrap",
                isCollapsed ? "justify-center p-3" : "gap-3 px-3 py-2.5",
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon size={isCollapsed ? 18 : 16} strokeWidth={1.8} className="shrink-0 opacity-70" />
              {!isCollapsed && <span>{label}</span>}
            </Link>
          );
        })}

        <div className={cn("mt-2 flex items-center rounded-xl py-2.5 transition-all overflow-hidden", isCollapsed ? "justify-center px-1" : "gap-3 px-2")}>
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white shadow-sm"
            style={{ background: "linear-gradient(135deg, var(--bronze), #8B6040)" }}
            title={isCollapsed ? user?.name || "User" : undefined}
          >
            {initials}
          </div>
          {!isCollapsed && (
            <div className="flex flex-1 items-center min-w-0 overflow-hidden justify-between gap-2">
              <div className="flex-1 min-w-0 pr-1 overflow-hidden">
                <p className="truncate text-xs font-medium text-foreground">{user?.name ?? "User"}</p>
                <p className="truncate text-[10px] text-muted-foreground">{user?.email ?? ""}</p>
              </div>
              <button
                title="Sign out"
                type="button"
                onClick={() => void onSignOut()}
                className="shrink-0 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground active:scale-[0.97]"
              >
                <LogOut size={14} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ProductShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  
  useEffect(() => {
    const stored = localStorage.getItem("ittera_sidebar_collapsed");
    if (stored === "true") {
      setIsCollapsed(true);
    }
  }, []);

  const handleToggleCollapse = () => {
    setIsCollapsed(prev => {
      const next = !prev;
      localStorage.setItem("ittera_sidebar_collapsed", next.toString());
      return next;
    });
  };

  const closeMobile = () => setMobileOpen(false);
  const productError = useProductStore((s) => s.error);
  const clearProductError = useProductStore((s) => s.clearError);

  const sidebarWidthClass = isCollapsed ? "w-[76px]" : "w-64";
  const contentMarginClass = isCollapsed ? "lg:ml-[76px]" : "lg:ml-64";

  return (
    <div className="flex min-h-screen bg-background">
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 hidden flex-shrink-0 flex-col lg:flex transition-all duration-300 ease-in-out",
          sidebarWidthClass
        )}
        style={{
          background: "var(--card)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <ProductSidebar 
          pathname={pathname} 
          onNavigate={() => {}} 
          user={user} 
          onSignOut={signOut} 
          isCollapsed={isCollapsed}
          onToggleCollapse={handleToggleCollapse}
        />
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
          "fixed inset-y-0 left-0 z-50 flex w-64 flex-col lg:hidden",
          "transition-transform duration-[220ms] cubic-bezier(0.32,0.72,0,1)",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
        style={{
          background: "var(--card)",
          borderRight: "1px solid var(--border)",
        }}
      >
        <ProductSidebar 
          pathname={pathname} 
          onNavigate={closeMobile} 
          user={user} 
          onSignOut={signOut} 
          isCollapsed={false}
        />
      </aside>

      <div className={cn("flex flex-1 flex-col transition-all duration-300 ease-in-out", contentMarginClass)}>
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
