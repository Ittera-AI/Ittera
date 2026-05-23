"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  ShieldCheck,
  UserCheck,
  UserX,
  Loader2,
  Search,
  Mail,
  Clock,
  ChevronLeft,
  Users,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  fetchAdminWaitlistEntries,
  approveWaitlistUser,
  revokeWaitlistUser,
  type AdminWaitlistEntry
} from "@/services/admin";
import { ROUTES } from "@/lib/routes";

export default function AdminDashboard() {
  const router = useRouter();
  const { isAdmin, sessionLoading } = useAuth() as any;
  const [entries, setEntries] = useState<AdminWaitlistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [processingEmails, setProcessingEmails] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!sessionLoading && !isAdmin) {
      router.replace("/dashboard");
    }
  }, [isAdmin, sessionLoading, router]);

  useEffect(() => {
    if (isAdmin) {
      loadEntries();
    }
  }, [isAdmin]);

  const loadEntries = async () => {
    try {
      const data = await fetchAdminWaitlistEntries();
      setEntries(data);
    } catch (err) {
      console.error("Failed to fetch entries:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (email: string) => {
    setProcessingEmails((prev) => new Set(prev).add(email));
    try {
      await approveWaitlistUser(email);
      setEntries((prev) =>
        prev.map((e) =>
          e.email === email ? { ...e, access_approved: true, approved_at: new Date().toISOString() } : e
        )
      );
    } catch (err) {
      console.error("Failed to approve user:", err);
    } finally {
      setProcessingEmails((prev) => {
        const next = new Set(prev);
        next.delete(email);
        return next;
      });
    }
  };

  const handleRevoke = async (email: string) => {
    if (!window.confirm(`Are you sure you want to revoke access for ${email}?`)) return;
    setProcessingEmails((prev) => new Set(prev).add(email));
    try {
      await revokeWaitlistUser(email);
      setEntries((prev) =>
        prev.map((e) =>
          e.email === email ? { ...e, access_approved: false, approved_at: null } : e
        )
      );
    } catch (err) {
      console.error("Failed to revoke user:", err);
    } finally {
      setProcessingEmails((prev) => {
        const next = new Set(prev);
        next.delete(email);
        return next;
      });
    }
  };

  const filteredEntries = useMemo(() => {
    const term = search.toLowerCase();
    return entries.filter(
      (e) =>
        e.email.toLowerCase().includes(term) ||
        (e.name && e.name.toLowerCase().includes(term))
    );
  }, [entries, search]);

  const stats = useMemo(() => {
    const total = entries.length;
    const approved = entries.filter((e) => e.access_approved).length;
    const pending = total - approved;
    return { total, approved, pending };
  }, [entries]);

  if (sessionLoading || (!isAdmin && loading)) {
    return (
      <div className="flex min-h-[500px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--bronze)]" />
      </div>
    );
  }

  if (!isAdmin) return null;

  return (
    <div className="mx-auto max-w-6xl pb-16">
      <Link
        href={ROUTES.dashboard}
        className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--bronze)]/10 text-[var(--bronze)] ring-1 ring-[var(--bronze)]/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Admin Portal</h1>
          </div>
          <p className="text-base text-muted-foreground max-w-xl">
            Manage workspace access, review waitlist applications, and control user privileges across your platform.
          </p>
        </div>

        <div className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search users by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-11 w-full rounded-xl border border-border bg-card pl-10 pr-4 text-sm shadow-sm transition-all focus:border-[var(--bronze)] focus:outline-none focus:ring-2 focus:ring-[var(--bronze)]/20"
          />
        </div>
      </div>

      {!loading && (
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10 text-blue-500">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Users</p>
              <h3 className="text-2xl font-bold">{stats.total}</h3>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Approved</p>
              <h3 className="text-2xl font-bold">{stats.approved}</h3>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5 shadow-sm">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10 text-amber-500">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Pending Approval</p>
              <h3 className="text-2xl font-bold">{stats.pending}</h3>
            </div>
          </div>
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/30">
              <tr>
                <th className="px-6 py-4 font-semibold text-muted-foreground">User Information</th>
                <th className="px-6 py-4 font-semibold text-muted-foreground">Access Status</th>
                <th className="px-6 py-4 font-semibold text-muted-foreground">Date Joined</th>
                <th className="px-6 py-4 text-right font-semibold text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={4} className="py-24 text-center">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-[var(--bronze)]/50" />
                    <p className="mt-4 text-sm text-muted-foreground">Loading users...</p>
                  </td>
                </tr>
              ) : filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-24 text-center">
                    <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                      <Users className="h-8 w-8 text-muted-foreground/50" />
                    </div>
                    <p className="text-base font-medium text-foreground">No users found</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {search ? "Try adjusting your search terms." : "The waitlist is currently empty."}
                    </p>
                  </td>
                </tr>
              ) : (
                <AnimatePresence>
                  {filteredEntries.map((entry) => (
                    <motion.tr
                      key={entry.email}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="group transition-colors hover:bg-muted/30"
                    >
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-4">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/50 font-bold text-muted-foreground ring-1 ring-border">
                            {entry.name ? entry.name.charAt(0).toUpperCase() : entry.email.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-semibold text-foreground">{entry.name || "Unknown User"}</p>
                            <p className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                              <Mail className="h-3 w-3" />
                              {entry.email}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        {entry.access_approved ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                            Approved
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]" />
                            Pending
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-5">
                        <p className="flex items-center gap-1.5 text-muted-foreground font-medium">
                          <Clock className="h-4 w-4 opacity-70" />
                          {new Date(entry.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </p>
                      </td>
                      <td className="px-6 py-5 text-right">
                        <div className="flex justify-end gap-2">
                          {entry.access_approved ? (
                            <button
                              type="button"
                              onClick={() => handleRevoke(entry.email)}
                              disabled={processingEmails.has(entry.email)}
                              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-muted-foreground shadow-sm transition-all hover:bg-red-500/10 hover:text-red-600 hover:border-red-500/30 disabled:opacity-50"
                            >
                              {processingEmails.has(entry.email) ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <UserX className="h-4 w-4" />
                              )}
                              Revoke
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleApprove(entry.email)}
                              disabled={processingEmails.has(entry.email)}
                              className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--bronze)] px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all hover:bg-[var(--bronze)]/90 hover:shadow-md disabled:opacity-50"
                            >
                              {processingEmails.has(entry.email) ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <UserCheck className="h-4 w-4" />
                              )}
                              Approve
                            </button>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
