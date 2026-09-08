"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  BookOpen,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { RiskBadge } from "@/components/ui/risk-badge";
import type { RiskMatch } from "@/types/api";

const COMPLIANCE_STATUS_CONFIG = {
  COMPLIANT: {
    label: "Compliant",
    className: "text-emerald-300 bg-emerald-500/10 border-emerald-500/30",
  },
  PARTIALLY_COMPLIANT: {
    label: "Partial",
    className: "text-amber-300 bg-amber-500/10 border-amber-500/30",
  },
  NON_COMPLIANT: {
    label: "Non-Compliant",
    className: "text-red-300 bg-red-500/10 border-red-500/30",
  },
  UNKNOWN: {
    label: "Unknown",
    className: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
  },
};

const SEVERITY_CONFIG = {
  LOW: { color: "text-zinc-400", bg: "bg-zinc-500/20" },
  MEDIUM: { color: "text-amber-300", bg: "bg-amber-500/10" },
  HIGH: { color: "text-orange-300", bg: "bg-orange-500/10" },
  CRITICAL: { color: "text-red-300", bg: "bg-red-500/10" },
};

interface ComplianceResultCardProps {
  match: RiskMatch;
  index: number;
}

export function ComplianceResultCard({
  match,
  index,
}: ComplianceResultCardProps) {
  const [expanded, setExpanded] = useState(index === 0);
  const statusConfig = COMPLIANCE_STATUS_CONFIG[match.compliance_status];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.35, ease: "easeOut" }}
      className="glass overflow-hidden rounded-xl"
      id={`compliance-card-${index}`}
    >
      {/* Card Header */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="flex w-full items-start justify-between gap-4 p-4 text-left transition-colors hover:bg-white/[0.03] lg:p-5"
      >
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            {/* Regulator code badge */}
            <span className="rounded border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-blue-300">
              {match.regulatory_clause.regulator_code}
            </span>
            <span className="text-xs text-zinc-500">
              Clause {match.regulatory_clause.clause_number}
            </span>
            {/* Compliance status */}
            <span
              className={cn(
                "rounded border px-2 py-0.5 text-[10px] font-semibold",
                statusConfig.className,
              )}
            >
              {statusConfig.label}
            </span>
          </div>
          <p className="line-clamp-2 text-sm text-zinc-300">
            {match.regulatory_clause.text}
          </p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <RiskBadge score={match.risk_score} size="sm" />
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-zinc-500" />
          ) : (
            <ChevronDown className="h-4 w-4 text-zinc-500" />
          )}
        </div>
      </button>

      {/* Expanded Content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="border-t border-white/5 p-4 lg:p-5">
              <div className="grid gap-4 lg:grid-cols-2">
                {/* Left: Regulatory Clause */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    <BookOpen className="h-3.5 w-3.5" />
                    Regulatory Clause
                  </div>
                  <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
                    <p className="mb-1 text-xs font-medium text-blue-300">
                      {match.regulatory_clause.regulation_title} ·{" "}
                      {match.regulatory_clause.clause_number}
                    </p>
                    <p className="text-sm leading-relaxed text-zinc-300">
                      {match.regulatory_clause.text}
                    </p>
                    <p className="mt-2 text-[10px] text-zinc-600">
                      Similarity:{" "}
                      {(match.regulatory_clause.similarity_score * 100).toFixed(
                        1,
                      )}
                      %
                    </p>
                  </div>
                </div>

                {/* Right: Policy Chunks */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    <FileText className="h-3.5 w-3.5" />
                    Policy Matches ({match.policy_chunks.length})
                  </div>
                  <div className="space-y-2">
                    {match.policy_chunks.length === 0 ? (
                      <p className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-300">
                        No matching policy content found.
                      </p>
                    ) : (
                      match.policy_chunks.slice(0, 3).map((chunk) => (
                        <div
                          key={chunk.id}
                          className="rounded-lg border border-white/5 bg-white/[0.02] p-3"
                        >
                          <p className="mb-1 text-[10px] font-medium text-zinc-500">
                            {chunk.document_title} · Chunk {chunk.chunk_index}
                          </p>
                          <p className="line-clamp-3 text-sm leading-relaxed text-zinc-400">
                            {chunk.text}
                          </p>
                          <p className="mt-1.5 text-[10px] text-zinc-600">
                            Match:{" "}
                            {(chunk.similarity_score * 100).toFixed(1)}%
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* AI Reasoning */}
              {match.reasoning && (
                <div className="mt-4 rounded-lg border border-white/5 bg-white/[0.02] p-3">
                  <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    AI Analysis
                  </p>
                  <p className="text-sm leading-relaxed text-zinc-400">
                    {match.reasoning}
                  </p>
                </div>
              )}

              {/* Identified Gaps */}
              {match.identified_gaps.length > 0 && (
                <div className="mt-3 space-y-1.5">
                  <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                    Identified Gaps
                  </p>
                  {match.identified_gaps.map((gap, i) => {
                    const cfg = SEVERITY_CONFIG[gap.severity];
                    return (
                      <div
                        key={i}
                        className={cn(
                          "flex items-start gap-2 rounded-lg p-2.5 text-sm",
                          cfg.bg,
                        )}
                      >
                        <span
                          className={cn(
                            "mt-0.5 shrink-0 rounded px-1 py-0.5 text-[9px] font-bold uppercase",
                            cfg.color,
                          )}
                        >
                          {gap.severity}
                        </span>
                        <span className="text-zinc-300">{gap.description}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
