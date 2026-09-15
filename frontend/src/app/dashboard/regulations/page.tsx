"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  BookOpen,
  Upload,
  Search,
  RefreshCw,
  ChevronRight,
  Clock,
  CheckCircle2,
  Loader2,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { listRegulations } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";
import { DemoBadge } from "@/components/shared/DemoBadge";
import type { Regulation } from "@/types/api";

const MOCK_REGULATIONS: Regulation[] = [
  {
    id: "reg_001",
    title: "RBI Master Direction on KYC 2023",
    regulator_code: "RBI",
    version: "v3.2",
    status: "COMPLETED",
    clause_count: 142,
    uploaded_at: "2024-01-15T10:30:00Z",
    uploaded_by: "admin@rbi.org.in",
  },
  {
    id: "reg_002",
    title: "SEBI LODR Regulations 2015 (Amended 2023)",
    regulator_code: "SEBI",
    version: "v2.1",
    status: "COMPLETED",
    clause_count: 89,
    uploaded_at: "2024-02-20T14:15:00Z",
    uploaded_by: "compliance@sebi.gov.in",
  },
];

const STATUS_CONFIG: Record<
  string,
  { icon: React.ReactNode; label: string; className: string }
> = {
  COMPLETED: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Ready",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  completed: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Ready",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  PROCESSING: {
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
    label: "Processing",
    className: "text-blue-300 bg-blue-500/10 border-blue-500/30",
  },
  processing: {
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
    label: "Processing",
    className: "text-blue-300 bg-blue-500/10 border-blue-500/30",
  },
  PENDING: {
    icon: <Clock className="h-3.5 w-3.5" />,
    label: "Pending",
    className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
  },
  pending: {
    icon: <Clock className="h-3.5 w-3.5" />,
    label: "Pending",
    className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
  },
  FAILED: {
    icon: <XCircle className="h-3.5 w-3.5" />,
    label: "Failed",
    className: "text-red-300 bg-red-500/10 border-red-500/30",
  },
  failed: {
    icon: <XCircle className="h-3.5 w-3.5" />,
    label: "Failed",
    className: "text-red-300 bg-red-500/10 border-red-500/30",
  },
};

const CODE_COLORS: Record<string, string> = {
  RBI: "text-orange-300 bg-orange-500/10 border-orange-500/30",
  SEBI: "text-blue-300 bg-blue-500/10 border-blue-500/30",
  IRDAI: "text-violet-300 bg-violet-500/10 border-violet-500/30",
  GDPR: "text-sky-300 bg-sky-500/10 border-sky-500/30",
  ISO: "text-zinc-300 bg-zinc-500/10 border-zinc-500/30",
  OTHER: "text-zinc-400 bg-zinc-600/10 border-zinc-600/30",
};

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function RegulationsPage() {
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const { user } = useAuth();
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const canEdit = user?.role === "ADMIN" || user?.role === "REGULATOR";

  const fetchRegulations = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setErrorMsg(null);

    try {
      const data = await listRegulations();
      const regList = Array.isArray(data) ? data : (data?.items ?? []);
      setRegulations(regList);
    } catch (err: unknown) {
      if (isDemoMode) {
        setRegulations(MOCK_REGULATIONS);
      } else {
        setRegulations([]);
        setErrorMsg(
          err instanceof Error ? err.message : "Failed to fetch regulations from API.",
        );
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [isDemoMode]);

  useEffect(() => {
    fetchRegulations(true);
  }, [fetchRegulations]);

  // Auto-poll if any regulation is in PENDING or PROCESSING state
  useEffect(() => {
    const hasPendingOrProcessing = regulations.some((r) => {
      const s = (r.status || "").toLowerCase();
      return s === "pending" || s === "processing";
    });

    if (!hasPendingOrProcessing) return;

    const interval = setInterval(() => {
      fetchRegulations(false);
    }, 4000);

    return () => clearInterval(interval);
  }, [regulations, fetchRegulations]);

  const filtered = regulations.filter(
    (r) =>
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.regulator_code.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="mx-auto max-w-5xl space-y-6"
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-blue-500/30 bg-blue-500/10">
            <BookOpen className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight">
                Regulation Library
              </h1>
              {isDemoMode && <DemoBadge />}
            </div>
            <p className="text-sm text-zinc-500">
              {regulations.length} regulatory document
              {regulations.length !== 1 ? "s" : ""} indexed
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            id="refresh-regulations-btn"
            onClick={() => fetchRegulations(true)}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-zinc-300 transition-all hover:bg-white/10 disabled:opacity-40"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-blue-400" : ""}`} />
            Refresh
          </button>
          {canEdit && (
            <Link
              href="/dashboard/regulations/upload"
              id="upload-regulation-link"
              className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-all hover:from-blue-500 hover:to-blue-400"
            >
              <Upload className="h-4 w-4" />
              Upload Regulation
            </Link>
          )}
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm font-medium">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          id="regulation-search"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by title or regulator…"
          className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-zinc-300 placeholder-zinc-600 outline-none transition-all focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30"
        />
      </div>

      {/* Table */}
      <div className="glass overflow-hidden rounded-xl">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-16 text-sm text-zinc-500">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Loading regulations…
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-sm text-zinc-500">
            No regulations found.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-left">
                <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                  Regulation
                </th>
                <th className="hidden px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 sm:table-cell">
                  Regulator
                </th>
                <th className="hidden px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 md:table-cell">
                  Version
                </th>
                <th className="hidden px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 lg:table-cell">
                  Clauses
                </th>
                <th className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                  Status
                </th>
                <th className="hidden px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-500 xl:table-cell">
                  Uploaded
                </th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {filtered.map((reg, i) => {
                const statusCfg = STATUS_CONFIG[reg.status] || {
                  icon: <Clock className="h-3.5 w-3.5" />,
                  label: reg.status,
                  className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
                };
                const codeCls = CODE_COLORS[reg.regulator_code] || CODE_COLORS.OTHER;
                return (
                  <motion.tr
                    key={reg.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="group transition-colors hover:bg-white/[0.03]"
                  >
                    <td className="px-4 py-3">
                      <p className="font-medium text-zinc-200">{reg.title}</p>
                    </td>
                    <td className="hidden px-4 py-3 sm:table-cell">
                      <span
                        className={`inline-flex rounded border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${codeCls}`}
                      >
                        {reg.regulator_code}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 text-zinc-500 md:table-cell">
                      {reg.version}
                    </td>
                    <td className="hidden px-4 py-3 text-zinc-500 lg:table-cell">
                      {reg.clause_count !== undefined ? reg.clause_count : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold ${statusCfg.className}`}
                      >
                        {statusCfg.icon}
                        {statusCfg.label}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 text-zinc-600 xl:table-cell">
                      {reg.uploaded_at ? formatDate(reg.uploaded_at) : "—"}
                    </td>
                    <td className="px-3 py-3">
                      <ChevronRight className="h-4 w-4 text-zinc-600 opacity-0 transition-opacity group-hover:opacity-100" />
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </motion.div>
  );
}
