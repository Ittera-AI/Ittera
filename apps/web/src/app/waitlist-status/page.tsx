"use client";

import { useEffect, useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { ROUTES } from "@/lib/routes";
import { api } from "@/lib/api";
import {
  fetchWaitlistMemberStatus,
} from "@/services/waitlist-access";
import WaitlistStatusView, {
  type WaitlistStats,
} from "@/components/waitlist/WaitlistStatusView";

const EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

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

  const principalKey = user?.id ?? null;
  const principalKeyRef = useRef(principalKey);
  const memberRequestGenerationRef = useRef(0);
  principalKeyRef.current = principalKey;

  const [refreshing, setRefreshing] = useState(false);
  const [justRefreshed, setJustRefreshed] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [stats, setStats] = useState<WaitlistStats | null>(null);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [memberPrincipalKey, setMemberPrincipalKey] = useState<string | null>(null);
  const [memberPosition, setMemberPosition] = useState<number | null>(null);
  const [positionChecked, setPositionChecked] = useState(false);
  const [positionError, setPositionError] = useState<string | null>(null);

  const loadMemberStatus = useCallback(async () => {
    const requestPrincipal = principalKeyRef.current;
    const requestGeneration = ++memberRequestGenerationRef.current;
    if (!requestPrincipal) return null;

    const { status, error } = await fetchWaitlistMemberStatus();
    if (
      requestGeneration !== memberRequestGenerationRef.current ||
      requestPrincipal !== principalKeyRef.current
    ) {
      return null;
    }

    setMemberPrincipalKey(requestPrincipal);
    if (status) {
      setMemberPosition(status.position);
      setPositionError(null);
      setStats((prev) => ({
        total_joined: status.total_joined,
        total_seats: status.total_seats,
        remaining_seats: status.remaining_seats,
        recent_joiners: prev?.recent_joiners ?? [],
      }));
    } else {
      setMemberPosition(null);
      setPositionError(error);
    }
    setPositionChecked(true);
    return status;
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await api.waitlist.stats();
      setStats(data);
      setStatsError(null);
      return true;
    } catch {
      // Keep any real member-derived aggregate data rather than replacing it
      // with invented zero/100 availability.
      setStatsError("Live cohort availability is unavailable. Refresh to try again.");
      return false;
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
    memberRequestGenerationRef.current += 1;
    setMemberPrincipalKey(principalKey);
    setMemberPosition(null);
    setPositionChecked(false);
    setPositionError(null);
    setRefreshing(false);
    setJustRefreshed(false);
    setRefreshError(null);

    if (!principalKey || hasWorkspaceAccess) return;
    void loadMemberStatus();

    return () => {
      memberRequestGenerationRef.current += 1;
    };
  }, [principalKey, hasWorkspaceAccess, loadMemberStatus]);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const handleRefresh = useCallback(async () => {
    const refreshPrincipal = principalKeyRef.current;
    if (refreshing || !refreshPrincipal) return;

    setRefreshing(true);
    setJustRefreshed(false);
    setRefreshError(null);
    try {
      const approved = await refreshWorkspaceAccess();
      if (principalKeyRef.current !== refreshPrincipal) return;

      const status = await loadMemberStatus();
      if (principalKeyRef.current !== refreshPrincipal) return;

      await loadStats();
      if (principalKeyRef.current !== refreshPrincipal) return;

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
      if (principalKeyRef.current === refreshPrincipal) {
        setRefreshError("Could not check status. Make sure the API is running and try again.");
      }
    } finally {
      if (principalKeyRef.current === refreshPrincipal) setRefreshing(false);
    }
  }, [refreshing, refreshWorkspaceAccess, loadMemberStatus, loadStats, router]);

  const handleSignOut = useCallback(async () => {
    await signOut();
    router.replace(ROUTES.home);
  }, [signOut, router]);

  const checking = sessionLoading;
  const hasCurrentMemberState =
    principalKey !== null && memberPrincipalKey === principalKey;
  const currentMemberPosition = hasCurrentMemberState ? memberPosition : null;
  const currentPositionChecked = hasCurrentMemberState && positionChecked;
  const currentPositionError = hasCurrentMemberState ? positionError : null;
  const displayPosition = currentMemberPosition ?? waitlistPosition;
  const positionLoading =
    !currentPositionChecked && displayPosition == null && !currentPositionError;
  const statusError = refreshError ?? currentPositionError ?? statsError;

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
            positionError={currentPositionError}
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
