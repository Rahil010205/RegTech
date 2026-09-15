"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Database,
  Layers,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { fetchHealth } from "@/lib/api-client";
import { RoleGuard } from "@/components/shared/RoleGuard";
import { DemoBadge } from "@/components/shared/DemoBadge";
import type { BackendHealthResponse } from "@/types/api";

const DEMO_HEALTH: BackendHealthResponse = {
  status: "ok",
  db: { connected: true, error: null },
  qdrant: { connected: true, error: null },
};

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {ok && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
      )}
      <span
        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${
          ok ? "bg-emerald-400" : "bg-red-400"
        }`}
      />
    </span>
  );
}

export default function SystemHealthPage() {
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const [health, setHealth] = useState<BackendHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setErrorMsg(null);

    fetchHealth()
      .then((data) => {
        setHealth(data);
        setErrorMsg(null);
      })
      .catch((err: unknown) => {
        if (isDemoMode) {
          setHealth(DEMO_HEALTH);
        } else {
          setHealth(null);
          setErrorMsg(
            err instanceof Error
              ? `API Error: ${err.message}`
              : "Failed to connect to backend health endpoint.",
          );
        }
      })
      .finally(() => {
        setLoading(false);
        setLastChecked(new Date());
      });
  }, [isDemoMode]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30_000);
    return () => clearInterval(interval);
  }, [refresh]);

  const allOk = health?.status === "ok" && health?.db?.connected && health?.qdrant?.connected;

  return (
    <RoleGuard allow={["ADMIN"]}>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="mx-auto max-w-3xl space-y-6"
      >
        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl border ${
                allOk
                  ? "border-emerald-500/30 bg-emerald-500/10"
                  : "border-red-500/30 bg-red-500/10"
              }`}
            >
              <Activity
                className={`h-5 w-5 ${allOk ? "text-emerald-400" : "text-red-400"}`}
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold tracking-tight">System Health</h1>
                {isDemoMode && <DemoBadge />}
              </div>
              <p className="text-sm text-zinc-500">
                Backend readiness check (/api/v1/health/ready) · auto-refreshes every 30s
              </p>
            </div>
          </div>
          <button
            id="refresh-health-btn"
            onClick={refresh}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-zinc-400 transition-all hover:bg-white/[0.06] hover:text-zinc-200 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm font-medium">
            <XCircle className="h-5 w-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Overall status banner */}
        {health && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`flex items-center gap-3 rounded-xl border p-4 ${
              allOk
                ? "border-emerald-500/20 bg-emerald-500/5"
                : "border-amber-500/20 bg-amber-500/5"
            }`}
          >
            {allOk ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-amber-400" />
            )}
            <div className="flex-1">
              <p
                className={`font-semibold ${
                  allOk ? "text-emerald-300" : "text-amber-300"
                }`}
              >
                {allOk ? "All Infrastructure Services Operational" : "Degraded Service Detected"}
              </p>
              <p className="text-xs text-zinc-500 mt-0.5">
                Status: <span className="font-mono font-bold text-zinc-300">{health.status}</span> · Last checked{" "}
                {lastChecked
                  ? lastChecked.toLocaleTimeString("en-IN", {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })
                  : "—"}
              </p>
            </div>
          </motion.div>
        )}

        {/* Real Service status cards */}
        {health && (
          <div className="grid gap-3 sm:grid-cols-2">
            {/* Database Card */}
            <div className="glass flex items-center gap-4 rounded-xl p-4">
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${
                  health.db.connected
                    ? "border-emerald-500/20 bg-emerald-500/5"
                    : "border-red-500/20 bg-red-500/5"
                }`}
              >
                <Database
                  className={`h-5 w-5 ${
                    health.db.connected ? "text-emerald-400" : "text-red-400"
                  }`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-200">PostgreSQL Database</p>
                <p
                  className={`text-xs ${
                    health.db.connected ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {health.db.connected
                    ? "Connected & healthy"
                    : health.db.error || "Connection error"}
                </p>
              </div>
              <StatusDot ok={health.db.connected} />
            </div>

            {/* Qdrant Vector DB Card */}
            <div className="glass flex items-center gap-4 rounded-xl p-4">
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${
                  health.qdrant.connected
                    ? "border-emerald-500/20 bg-emerald-500/5"
                    : "border-red-500/20 bg-red-500/5"
                }`}
              >
                <Layers
                  className={`h-5 w-5 ${
                    health.qdrant.connected ? "text-emerald-400" : "text-red-400"
                  }`}
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-zinc-200">Qdrant Vector DB</p>
                <p
                  className={`text-xs ${
                    health.qdrant.connected ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {health.qdrant.connected
                    ? "Connected & healthy"
                    : health.qdrant.error || "Connection error"}
                </p>
              </div>
              <StatusDot ok={health.qdrant.connected} />
            </div>
          </div>
        )}

        {loading && !health && (
          <div className="grid gap-3 sm:grid-cols-2">
            {[0, 1].map((i) => (
              <div
                key={i}
                className="glass animate-pulse rounded-xl p-4 space-y-2"
              >
                <div className="h-4 w-32 rounded bg-white/5" />
                <div className="h-3 w-24 rounded bg-white/5" />
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </RoleGuard>
  );
}
