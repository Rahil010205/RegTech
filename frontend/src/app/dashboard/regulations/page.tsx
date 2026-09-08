"use client";

import { useState, useEffect } from "react";
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
} from "lucide-react";
import { listRegulations } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";
import type { Regulation, ProcessingStatus, RegulatorCode } from "@/types/api";

// ─── Mock data for demo ───────────────────────────────────────────────────────
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
  {
    id: "reg_003",
    title: "IRDAI Corporate Governance Guidelines",
    regulator_code: "IRDAI",
    version: "v1.0",
    status: "PROCESSING",
    clause_count: 0,
    uploaded_at: "2024-03-05T09:00:00Z",
    uploaded_by: "admin@irdai.gov.in",
  },
  {
    id: "reg_004",
    title: "GDPR Article 17 — Right to Erasure",
    regulator_code: "GDPR",
    version: "2018",
    status: "COMPLETED",
    clause_count: 34,
    uploaded_at: "2024-01-08T16:45:00Z",
    uploaded_by: "legal@eu-compliance.org",
  },
  {
    id: "reg_005",
    title: "ISO 27001:2022 Information Security",
    regulator_code: "ISO",
    version: "2022",
    status: "COMPLETED",
    clause_count: 203,
    uploaded_at: "2023-12-01T11:20:00Z",
    uploaded_by: "isms@org.com",
  },
];

const STATUS_CONFIG: Record<
  ProcessingStatus,
  { icon: React.ReactNode; label: string; className: string }
> = {
  COMPLETED: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Ready",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  PROCESSING: {
    icon: <Loader2 className="h-3.5 w-3.5 animate-spin" />,
    label: "Processing",
    className: "text-blue-300 bg-blue-500/10 border-blue-500/30",
  },
  PENDING: {
    icon: <Clock className="h-3.5 w-3.5" />,
    label: "Pending",
    className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
  },
  FAILED: {
    icon: <XCircle className="h-3.5 w-3.5" />,
    label: "Failed",
    className: "text-red-300 bg-red-500/10 border-red-500/30",
  },
};

const CODE_COLORS: Record<RegulatorCode, string> = {
  RBI: "text-orange-300 bg-orange-500/10 border-orange-500/30",
  SEBI: "text-blue-300 bg-blue-500/10 border-blue-500/30",
  IRDAI: "text-violet-300 bg-violet-500/10 border-violet-500/30",
  GDPR: "text-sky-300 bg-sky-500/10 border-sky-500/30",
  ISO: "text-zinc-300 bg-zinc-500/10 border-zinc-500/30",
  OTHER: "text-zinc-400 bg-zinc-600/10 border-zinc-600/30",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function RegulationsPage() {
  const { user } = useAuth();
  const [regulations, setRegulations] = useState<Regulation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const canEdit = user?.role === "ADMIN" || user?.role === "REGULATOR";

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listRegulations()
      .then((data) => {
        if (!cancelled) setRegulations(data);
      })
      .catch(() => {
        if (!cancelled) setRegulations(MOCK_REGULATIONS);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
            <h1 className="text-xl font-semibold tracking-tight">
              Regulation Library
            </h1>
            <p className="text-sm text-zinc-500">
              {regulations.length} regulatory document
              {regulations.length !== 1 ? "s" : ""} indexed
            </p>
          </div>
        </div>
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
                const statusCfg = STATUS_CONFIG[reg.status];
                const codeCls = CODE_COLORS[reg.regulator_code];
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
                      {reg.status === "COMPLETED" ? reg.clause_count : "—"}
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
                      {formatDate(reg.uploaded_at)}
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
