"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  FileStack,
  Upload,
  Search,
  RefreshCw,
  CheckCircle2,
  Loader2,
  Clock,
  XCircle,
  Building2,
  AlertCircle,
} from "lucide-react";
import { listOrgDocuments } from "@/lib/api-client";
import { useOrganizations } from "@/hooks/use-organizations";
import { DemoBadge } from "@/components/shared/DemoBadge";
import type { PolicyDocument } from "@/types/api";

/**
 * Demo-only mock policies. In normal mode, only real API data is shown.
 * Fields match the backend DocumentResponse schema (filename, doc_type, created_at).
 */
const DEMO_POLICIES: PolicyDocument[] = [
  {
    id: "doc_001",
    org_id: "demo",
    filename: "Company KYC Standard Operating Procedure.pdf",
    doc_type: "KYC_SOP",
    status: "COMPLETED",
    created_at: "2024-03-10T10:00:00Z",
  },
  {
    id: "doc_002",
    org_id: "demo",
    filename: "Anti-Money Laundering Policy 2024.pdf",
    doc_type: "AML_POLICY",
    status: "COMPLETED",
    created_at: "2024-02-28T14:00:00Z",
  },
];

const STATUS_CONFIG: Record<
  string,
  { icon: React.ReactNode; label: string; className: string }
> = {
  COMPLETED: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Indexed",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  completed: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Indexed",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  processed: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Processed",
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
  uploaded: {
    icon: <Clock className="h-3.5 w-3.5" />,
    label: "Uploaded",
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

/** Strip .pdf extension and truncate long filenames for display */
function displayName(filename: string): string {
  return filename.replace(/\.pdf$/i, "").trim();
}

export default function PoliciesPage() {
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
  const { activeOrgId, activeOrganization } = useOrganizations();
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    if (!activeOrgId) {
      // No org selected: show demo data in demo mode, empty list in normal mode
      setPolicies(isDemoMode ? DEMO_POLICIES : []);
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    listOrgDocuments(activeOrgId)
      .then((data) => {
        if (cancelled) return;
        const docsList = Array.isArray(data) ? data : (data?.items ?? []);
        setPolicies(docsList);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (isDemoMode) {
          setPolicies(DEMO_POLICIES);
        } else {
          setPolicies([]);
          setErrorMsg(
            err instanceof Error ? err.message : "Failed to load policy documents from server.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeOrgId, isDemoMode]);

  const filtered = policies.filter((p) =>
    (p.filename ?? "").toLowerCase().includes(search.toLowerCase()),
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
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10">
            <FileStack className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight">My Policies</h1>
              {isDemoMode && <DemoBadge />}
            </div>
            <p className="text-sm text-zinc-500">
              {policies.length} document{policies.length !== 1 ? "s" : ""}{" "}
              uploaded · Org:{" "}
              {activeOrgId ? (
                <span className="font-mono text-zinc-300">{activeOrganization?.name || activeOrgId}</span>
              ) : (
                <span className="text-amber-400 font-medium">(none selected)</span>
              )}
            </p>
          </div>
        </div>
        <Link
          href="/dashboard/policies/upload"
          id="upload-policy-link"
          className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all hover:from-emerald-500 hover:to-emerald-400"
        >
          <Upload className="h-4 w-4" />
          Upload Policy
        </Link>
      </div>

      {!activeOrgId && !isDemoMode && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-300 text-sm">
          <Building2 className="h-5 w-5 shrink-0" />
          <span>Please select an active organization in the top navigation bar to view its policy documents.</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400 text-sm font-medium">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
        <input
          id="policy-search"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search policy documents…"
          className="w-full rounded-lg border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-zinc-300 placeholder-zinc-600 outline-none transition-all focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30"
        />
      </div>

      {/* Cards */}
      {loading ? (
        <div className="flex items-center justify-center gap-2 py-16 text-sm text-zinc-500">
          <RefreshCw className="h-4 w-4 animate-spin" />
          Loading documents…
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-sm text-zinc-500">
          No policy documents found.{" "}
          <Link
            href="/dashboard/policies/upload"
            className="text-emerald-400 hover:underline"
          >
            Upload one.
          </Link>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {filtered.map((doc, i) => {
            const statusCfg = STATUS_CONFIG[doc.status] || {
              icon: <Clock className="h-3.5 w-3.5" />,
              label: doc.status,
              className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
            };
            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06 }}
                className="glass rounded-xl p-4 transition-colors hover:bg-white/[0.03]"
              >
                <div className="mb-3 flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="truncate font-medium text-zinc-200">
                      {displayName(doc.filename)}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {doc.doc_type || "—"}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] font-semibold ${statusCfg.className}`}
                  >
                    {statusCfg.icon}
                    {statusCfg.label}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-zinc-600">
                  <span>{doc.created_at ? formatDate(doc.created_at) : "Just now"}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
