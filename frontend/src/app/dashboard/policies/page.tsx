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
} from "lucide-react";
import { listOrgDocuments, MOCK_ORG_ID } from "@/lib/api-client";
import type { PolicyDocument, ProcessingStatus } from "@/types/api";

const MOCK_POLICIES: PolicyDocument[] = [
  {
    id: "doc_001",
    org_id: MOCK_ORG_ID,
    title: "Company KYC Standard Operating Procedure",
    document_type: "KYC_SOP",
    status: "COMPLETED",
    chunk_count: 48,
    uploaded_at: "2024-03-10T10:00:00Z",
    uploaded_by: "compliance@acmecorp.com",
  },
  {
    id: "doc_002",
    org_id: MOCK_ORG_ID,
    title: "Anti-Money Laundering Policy 2024",
    document_type: "AML_POLICY",
    status: "COMPLETED",
    chunk_count: 32,
    uploaded_at: "2024-02-28T14:00:00Z",
    uploaded_by: "legal@acmecorp.com",
  },
  {
    id: "doc_003",
    org_id: MOCK_ORG_ID,
    title: "Enterprise Risk Management Framework",
    document_type: "RISK_FRAMEWORK",
    status: "PROCESSING",
    chunk_count: 0,
    uploaded_at: "2024-03-12T09:30:00Z",
    uploaded_by: "risk@acmecorp.com",
  },
  {
    id: "doc_004",
    org_id: MOCK_ORG_ID,
    title: "Q4 Internal Audit Report",
    document_type: "INTERNAL_AUDIT",
    status: "COMPLETED",
    chunk_count: 67,
    uploaded_at: "2024-01-20T16:00:00Z",
    uploaded_by: "audit@acmecorp.com",
  },
];

const STATUS_CONFIG: Record<
  ProcessingStatus,
  { icon: React.ReactNode; label: string; className: string }
> = {
  COMPLETED: {
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    label: "Indexed",
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

const DOC_TYPE_LABELS: Record<string, string> = {
  KYC_SOP: "KYC SOP",
  AML_POLICY: "AML Policy",
  RISK_FRAMEWORK: "Risk Framework",
  INTERNAL_AUDIT: "Internal Audit",
  OTHER: "Other",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listOrgDocuments(MOCK_ORG_ID)
      .then((data) => {
        if (!cancelled) setPolicies(data);
      })
      .catch(() => {
        if (!cancelled) setPolicies(MOCK_POLICIES);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = policies.filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase()),
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
            <h1 className="text-xl font-semibold tracking-tight">My Policies</h1>
            <p className="text-sm text-zinc-500">
              {policies.length} document{policies.length !== 1 ? "s" : ""}{" "}
              uploaded · Org:{" "}
              <span className="font-mono text-zinc-600">{MOCK_ORG_ID}</span>
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
            const statusCfg = STATUS_CONFIG[doc.status];
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
                      {doc.title}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {DOC_TYPE_LABELS[doc.document_type] ?? doc.document_type}
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
                  <span>
                    {doc.status === "COMPLETED" ? `${doc.chunk_count} chunks` : "—"}
                  </span>
                  <span>·</span>
                  <span>{formatDate(doc.uploaded_at)}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
