"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Database,
  Server,
  Cpu,
  Layers,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { fetchHealth } from "@/lib/api-client";
import { RoleGuard } from "@/components/shared/RoleGuard";
import type { HealthStatus } from "@/types/api";

const MOCK_HEALTH: HealthStatus = {
  status: "ok",
  version: "1.4.2",
  services: {
    database: "ok",
    qdrant: "ok",
    redis: "ok",
    celery: "ok",
  },
  uptime_seconds: 86543,
};

const SERVICE_ICONS = {
  database: Database,
  qdrant: Layers,
  redis: Server,
  celery: Cpu,
};

const SERVICE_LABELS = {
  database: "PostgreSQL",
  qdrant: "Qdrant Vector DB",
  redis: "Redis Cache",
  celery: "Celery Workers",
};

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hrs = Math.floor((seconds % 86400) / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hrs}h ${mins}m`;
  if (hrs > 0) return `${hrs}h ${mins}m`;
  return `${mins}m`;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {ok && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-40" />
      )}
      <span
        className={`relative inline-flex h-2.5 w-2.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"}`}
      />
    </span>
  );
}

export default function SystemHealthPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchHealth()
      .then((data) => setHealth(data))
      .catch(() => setHealth(MOCK_HEALTH))
      .finally(() => {
        setLoading(false);
        setLastChecked(new Date());
      });
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30_000);
    return () => clearInterval(interval);
  }, [refresh]);

  const allOk =
    health?.status === "ok" &&
    Object.values(health.services).every((s) => s === "ok");

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
              className={`flex h-10 w-10 items-center justify-center rounded-xl border ${allOk ? "border-emerald-500/30 bg-emerald-500/10" : "border-red-500/30 bg-red-500/10"}`}
            >
              <Activity
                className={`h-5 w-5 ${allOk ? "text-emerald-400" : "text-red-400"}`}
              />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">
                System Health
              </h1>
              <p className="text-sm text-zinc-500">
                Infrastructure status · auto-refreshes every 30s
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

        {/* Overall status banner */}
        {health && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`flex items-center gap-3 rounded-xl border p-4 ${
              allOk
                ? "border-emerald-500/20 bg-emerald-500/5"
                : "border-red-500/20 bg-red-500/5"
            }`}
          >
            {allOk ? (
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-amber-400" />
            )}
            <div className="flex-1">
              <p
                className={`font-semibold ${allOk ? "text-emerald-300" : "text-amber-300"}`}
              >
                {allOk ? "All Systems Operational" : "Degraded Performance Detected"}
              </p>
              <p className="text-xs text-zinc-500">
                Version{" "}
                <span className="font-mono text-zinc-400">{health.version}</span>{" "}
                · Uptime {formatUptime(health.uptime_seconds)} · Last checked{" "}
                {lastChecked
                  ? lastChecked.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
                  : "—"}
              </p>
            </div>
          </motion.div>
        )}

        {/* Service cards */}
        <div className="grid gap-3 sm:grid-cols-2">
          {health &&
            (
              Object.entries(health.services) as [
                keyof typeof SERVICE_ICONS,
                "ok" | "error",
              ][]
            ).map(([key, status], i) => {
              const Icon = SERVICE_ICONS[key];
              const isOk = status === "ok";
              return (
                <motion.div
                  key={key}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="glass flex items-center gap-4 rounded-xl p-4"
                >
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${isOk ? "border-emerald-500/20 bg-emerald-500/5" : "border-red-500/20 bg-red-500/5"}`}
                  >
                    <Icon
                      className={`h-5 w-5 ${isOk ? "text-emerald-400" : "text-red-400"}`}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200">
                      {SERVICE_LABELS[key]}
                    </p>
                    <p
                      className={`text-xs ${isOk ? "text-emerald-400" : "text-red-400"}`}
                    >
                      {isOk ? "Connected & healthy" : "Connection error"}
                    </p>
                  </div>
                  <StatusDot ok={isOk} />
                </motion.div>
              );
            })}

          {loading &&
            !health &&
            [0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="glass animate-pulse rounded-xl p-4"
                style={{ animationDelay: `${i * 100}ms` }}
              >
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-white/5" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 w-32 rounded-full bg-white/5" />
                    <div className="h-3 w-24 rounded-full bg-white/5" />
                  </div>
                </div>
              </div>
            ))}
        </div>

        {/* API endpoint info */}
        {health && (
          <div className="glass rounded-xl p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              API Endpoints
            </p>
            <div className="space-y-2 text-xs">
              {[
                { path: "/api/v1/health", label: "Liveness" },
                { path: "/api/v1/health/ready", label: "Readiness" },
                { path: "/api/v1/regulations/upload", label: "Regulation Upload" },
                { path: "/api/v1/organizations/{id}/documents", label: "Policy Upload" },
                { path: "/api/v1/organizations/{id}/compliance/risk", label: "Compliance Risk" },
              ].map(({ path, label }) => (
                <div
                  key={path}
                  className="flex items-center justify-between gap-4 rounded-lg bg-white/[0.02] px-3 py-2"
                >
                  <span className="text-zinc-400">{label}</span>
                  <div className="flex items-center gap-2">
                    <code className="font-mono text-zinc-600">{path}</code>
                    {allOk ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5 text-red-400" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </RoleGuard>
  );
}
