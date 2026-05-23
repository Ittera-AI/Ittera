"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/lib/routes";
import { apiFetch } from "@/services/api";
import {
  fetchWaitlistMemberStatus,
} from "@/services/waitlist-access";
import WaitlistStatusView, {
  type WaitlistStats,
} from "@/components/waitlist/WaitlistStatusView";

const EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

const FALLBACK_STATS: WaitlistStats = {
  total_joined: 0,
  total_seats: 100,
  remaining_seats: 100,
  recent_joiners: [],
};

export default function WaitlistStatusPage() {
  const router = useRouter();
  const {
    user,
    sessionLoading,
    workspaceAccessLoading,
    workspaceAccessChecked,
    hasWorkspaceAccess,
    waitlistPosition,
    refreshWorkspaceAccess,
    signOut,
  } = useAuth();

  const [refreshing, setRefreshing] = useState(false);
  const [justRefreshed, setJustRefreshed] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [stats, setStats] = useState<WaitlistStats>(FALLBACK_STATS);
  const [memberPosition, setMemberPosition] = useState<number | null>(null);
  const [positionChecked, setPositionChecked] = useState(false);
  const [positionError, setPositionError] = useState<string | null>(null);

  const loadMemberStatus = useCallback(async () => {
    const { status, error } = await fetchWaitlistMemberStatus();
    if (status) {
      setMemberPosition(status.position);
      setPositionError(null);
      setStats((prev) => ({
        total_joined: status.total_joined,
        total_seats: status.total_seats,
        remaining_seats: status.remaining_seats,
        recent_joiners: prev.recent_joiners,
      }));
    } else {
      setPositionError(error);
    }
    setPositionChecked(true);
    return status;
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await apiFetch<WaitlistStats>("/api/v1/waitlist");
      setStats(data);
    } catch {
      setStats(FALLBACK_STATS);
    }
  }, []);

  useEffect(() => {
    if (sessionLoading) return;
    if (!user) {
      router.replace(ROUTES.home);
      return;
    }
    if (hasWorkspaceAccess) {
      router.replace(ROUTES.dashboard);
      return;
    }
    if (!workspaceAccessChecked && !workspaceAccessLoading) {
      void refreshWorkspaceAccess();
    }
  }, [
    user,
    sessionLoading,
    workspaceAccessLoading,
    workspaceAccessChecked,
    hasWorkspaceAccess,
    refreshWorkspaceAccess,
    router,
  ]);

  useEffect(() => {
    if (!user || hasWorkspaceAccess) return;
    setPositionChecked(false);
    void loadMemberStatus();
  }, [user, hasWorkspaceAccess, loadMemberStatus]);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const handleRefresh = useCallback(async () => {
    if (refreshing) return;
    setRefreshing(true);
    setJustRefreshed(false);
    setRefreshError(null);
    try {
      const approved = await refreshWorkspaceAccess();
      const status = await loadMemberStatus();
      await loadStats();
      if (approved) {
        router.replace(ROUTES.dashboard);
        return;
      }
      if (!status?.position) {
        setRefreshError("Could not load queue position. Make sure the API is running and try again.");
      }
      setJustRefreshed(true);
      setTimeout(() => setJustRefreshed(false), 3000);
    } catch {
      setRefreshError("Could not check status. Make sure the API is running and try again.");
    } finally {
      setRefreshing(false);
    }
  }, [refreshing, refreshWorkspaceAccess, loadMemberStatus, loadStats, router]);

  const handleSignOut = useCallback(async () => {
    await signOut();
    router.replace(ROUTES.home);
  }, [signOut, router]);

  const checking = sessionLoading;
  const displayPosition = memberPosition ?? waitlistPosition;
  const positionLoading =
    !positionChecked && displayPosition == null && !positionError;
  const statusError = refreshError ?? positionError;

  return (
    <AnimatePresence mode="wait">
      {checking || !user ? (
        <motion.main
          key="loading"
          className="flex min-h-screen items-center justify-center bg-[var(--bg)]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="flex flex-col items-center gap-4">
            <div
              className="h-8 w-8 animate-spin rounded-full border-2 border-transparent"
              style={{
                borderTopColor: "var(--bronze)",
                borderRightColor: "rgba(163,138,112,0.15)",
              }}
            />
            <p className="text-sm text-[var(--text-muted)]">Loading your status…</p>
          </div>
        </motion.main>
      ) : (
        <motion.div
          key="content"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: EASE }}
        >
          <WaitlistStatusView
            user={user}
            waitlistPosition={displayPosition}
            positionLoading={positionLoading}
            positionError={positionError}
            stats={stats}
            refreshing={refreshing}
            justRefreshed={justRefreshed}
            refreshError={statusError}
            onRefresh={() => void handleRefresh()}
            onSignOut={() => void handleSignOut()}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
