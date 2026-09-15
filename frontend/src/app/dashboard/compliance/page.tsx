"use client";

import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import {
  Search,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  X,
  Building2,
  AlertCircle,
  FileText,
  AlertTriangle,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { useOrganizations } from "@/hooks/use-organizations";
import {
  searchRegulatoryClauses,
  evaluateComplianceRisk,
} from "@/lib/api-client";
import { DemoBadge } from "@/components/shared/DemoBadge";
import type {
  RegulatoryClauseResult,
  RiskScoringResponse,
} from "@/types/api";

const EXAMPLE_QUERIES = [
  "KYC customer due diligence requirements",
  "AML transaction monitoring obligations",
  "Data retention and record keeping",
  "Board reporting and governance",
  "Risk categorization and EDD procedures",
];

// Fallback mock risk response (demo mode only) — matches real RiskScoringResponse schema
function buildMockRiskResponse(clauseId: string, orgId: string): RiskScoringResponse {
  return {
    organization_id: orgId,
    regulatory_clause_id: clauseId,
    compliance_status: "PARTIALLY_COMPLIANT",
    risk_score: 42.5,
    risk_level: "MEDIUM",
    confidence: 0.72,
    explanation:
      "Demo Mode Analysis: The organization's policy documents demonstrate partial alignment with the selected regulatory clause. High-risk account review schedules and Board-level reporting frequency require adjustment. Assessed compliance risk score is 42.50 (MEDIUM). Status PARTIALLY_COMPLIANT contributes 20.00 points (weight 40%). Regulatory clause criticality is MEDIUM (0.50), contributing 10.00 points (weight 20%).",
    factor_breakdown: {
      compliance_severity: { value: 0.5, weight: 0.4, contribution: 20.0, description: "PARTIALLY_COMPLIANT status maps to 0.50 severity." },
      regulatory_criticality: { value: 0.5, weight: 0.2, contribution: 10.0, description: "Regulatory clause criticality is MEDIUM (0.50)." },
      gap_severity: { value: 0.5, weight: 0.15, contribution: 7.5, description: "Maximum identified gap severity is MEDIUM (0.50)." },
      evidence_strength: { value: 0.72, weight: 0.15, contribution: 10.8, description: "Average verified evidence similarity is 0.72." },
      confidence: { value: 0.72, weight: 0.10, contribution: 7.2, description: "Step 2B analysis confidence is 0.72." },
    },
    identified_gaps: [
      {
        description: "Policy does not specify review intervals for high-risk customers (semi-annual vs required quarterly).",
        severity: "MEDIUM",
      },
      {
        description: "Board reporting on AML metrics is on a semi-annual basis; clause requires quarterly reporting.",
        severity: "LOW",
      },
    ],
    created_at: new Date().toISOString(),
  };
}

const RISK_LEVEL_CLASSES: Record<string, string> = {
  CRITICAL: "border-red-500/40 bg-red-500/20 text-red-300",
  HIGH: "border-orange-500/40 bg-orange-500/20 text-orange-300",
  MEDIUM: "border-amber-500/40 bg-amber-500/20 text-amber-300",
  LOW: "border-emerald-500/40 bg-emerald-500/20 text-emerald-300",
};

const GAP_SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: "text-red-300 bg-red-500/10 border-red-500/30",
  HIGH: "text-orange-300 bg-orange-500/10 border-orange-500/30",
  MEDIUM: "text-amber-300 bg-amber-500/10 border-amber-500/30",
  LOW: "text-zinc-400 bg-zinc-500/10 border-zinc-500/30",
};

export default function CompliancePage() {
  const { activeOrgId, activeOrganization } = useOrganizations();
  const isDemoMode = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

  const [query, setQuery] = useState("");
  const [isSearchingClauses, setIsSearchingClauses] = useState(false);
  const [clauses, setClauses] = useState<RegulatoryClauseResult[]>([]);
  const [selectedClause, setSelectedClause] = useState<RegulatoryClauseResult | null>(null);

  const [isEvaluating, setIsEvaluating] = useState(false);
  const [riskResult, setRiskResult] = useState<RiskScoringResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  // Step 1: Search for regulatory clauses
  const handleClauseSearch = useCallback(
    async (searchQuery?: string) => {
      const q = (searchQuery ?? query).trim();
      if (!q) return;

      setQuery(q);
      setIsSearchingClauses(true);
      setErrorMsg(null);
      setRiskResult(null);
      setSelectedClause(null);
      setHasSearched(true);

      try {
        const data = await searchRegulatoryClauses(q, 5);
        const results = data?.results ?? [];
        setClauses(results);

        if (results.length === 0 && !isDemoMode) {
          setErrorMsg(`No regulatory clauses found matching "${q}". Ensure regulatory documents have been uploaded and indexed.`);
        } else if (results.length === 0 && isDemoMode) {
          // Demo mode mock clauses
          setClauses([
            {
              clause_id: "clause_rbi_kyc_001",
              document_id: "doc_rbi_kyc_2023",
              document_name: "RBI Master Direction on KYC 2023",
              regulator: "RBI",
              clause_number: "16(a)",
              text: "Every Regulated Entity (RE) shall establish and implement a Customer Due Diligence (CDD) policy that encompasses risk-based categorisation of customers, continuous transaction monitoring, and periodic review of high-risk accounts at intervals not exceeding twelve months.",
              similarity: 0.91,
            },
            {
              clause_id: "clause_rbi_kyc_031",
              document_id: "doc_rbi_kyc_2023",
              document_name: "RBI Master Direction on KYC 2023",
              regulator: "RBI",
              clause_number: "31(b)",
              text: "Regulated Entities must maintain KYC records for a minimum of eight years after the end of the business relationship in a retrievable and tamper-evident format.",
              similarity: 0.84,
            },
          ]);
        }
      } catch (err: unknown) {
        if (isDemoMode) {
          setClauses([
            {
              clause_id: "clause_rbi_kyc_001",
              document_id: "doc_rbi_kyc_2023",
              document_name: "RBI Master Direction on KYC 2023",
              regulator: "RBI",
              clause_number: "16(a)",
              text: "Every Regulated Entity (RE) shall establish and implement a Customer Due Diligence (CDD) policy that encompasses risk-based categorisation of customers, continuous transaction monitoring, and periodic review of high-risk accounts at intervals not exceeding twelve months.",
              similarity: 0.91,
            },
          ]);
        } else {
          const errStr = err instanceof Error ? err.message : String(err);
          const isTimeout =
            errStr.toLowerCase().includes("timeout") ||
            (typeof err === "object" && err !== null && "code" in err && (err as { code: unknown }).code === "ECONNABORTED");
          if (isTimeout) {
            setErrorMsg(
              "Semantic search timed out while loading the embedding model on cold start. The model is warming up; please click Search Clauses again.",
            );
          } else {
            setErrorMsg(
              err instanceof Error ? err.message : "Failed to search regulatory clauses. Ensure the API is running.",
            );
          }
        }
      } finally {
        setIsSearchingClauses(false);
      }
    },
    [query, isDemoMode],
  );

  // Step 2: Evaluate compliance risk for the selected regulatory clause
  const handleEvaluateRisk = useCallback(
    async (clause: RegulatoryClauseResult) => {
      if (!activeOrgId) {
        setErrorMsg("An active organization must be selected before evaluating compliance.");
        return;
      }

      setSelectedClause(clause);
      setIsEvaluating(true);
      setErrorMsg(null);
      setRiskResult(null);

      try {
        const result = await evaluateComplianceRisk(activeOrgId, clause.clause_id, 5, 0.5);
        setRiskResult(result);
      } catch (err: unknown) {
        if (isDemoMode) {
          await new Promise((r) => setTimeout(r, 800));
          setRiskResult(buildMockRiskResponse(clause.clause_id, activeOrgId));
        } else {
          setErrorMsg(
            err instanceof Error
              ? `Compliance Risk API Error: ${err.message}`
              : "Failed to evaluate compliance risk for selected clause.",
          );
        }
      } finally {
        setIsEvaluating(false);
      }
    },
    [activeOrgId, isDemoMode],
  );

  const handleClear = useCallback(() => {
    setQuery("");
    setClauses([]);
    setSelectedClause(null);
    setRiskResult(null);
    setErrorMsg(null);
    setHasSearched(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* No active org alert */}
      {!activeOrgId && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-amber-300">
          <Building2 className="h-5 w-5 shrink-0" />
          <div className="text-sm">
            <p className="font-semibold">No Active Organization Selected</p>
            <p className="text-xs text-amber-400/80">
              Please select or create an active organization in the top navigation to run compliance evaluations against organization policy documents.
            </p>
          </div>
        </div>
      )}

      {/* Main search card */}
      <motion.div
        layout
        animate={hasSearched ? { marginTop: 0 } : { marginTop: "4vh" }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="space-y-4"
      >
        {!hasSearched && (
          <div className="mb-6 text-center">
            <div className="mb-3 flex justify-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-600/20 to-violet-600/20 shadow-xl">
                <ShieldCheck className="h-7 w-7 text-blue-400" />
              </div>
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Compliance Evaluation</h1>
            <p className="mt-1 text-sm text-zinc-500">
              Search regulatory clauses and evaluate compliance risk against your active organization policy documents.
            </p>
          </div>
        )}

        {/* Input */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-500" />
          <input
            ref={inputRef}
            id="compliance-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleClauseSearch()}
            placeholder="Search regulatory clause or compliance requirement..."
            className="w-full rounded-xl border border-white/10 bg-white/5 py-3.5 pl-12 pr-28 text-sm text-zinc-200 placeholder-zinc-600 outline-none shadow-lg transition-all focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30"
          />
          <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
            {(query || hasSearched) && (
              <button
                onClick={handleClear}
                className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:text-zinc-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <button
              id="compliance-search-btn"
              onClick={() => handleClauseSearch()}
              disabled={!query.trim() || isSearchingClauses}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md transition-all hover:bg-blue-500 disabled:opacity-40"
            >
              {isSearchingClauses ? (
                <>
                  <Sparkles className="h-3.5 w-3.5 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  Search Clauses
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Example queries */}
        {!hasSearched && (
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            {EXAMPLE_QUERIES.map((eq) => (
              <button
                key={eq}
                onClick={() => handleClauseSearch(eq)}
                className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-zinc-400 hover:border-white/20 hover:text-zinc-200 transition-all"
              >
                {eq}
              </button>
            ))}
          </div>
        )}
      </motion.div>

      {/* Loading state indicator with cold-start advice */}
      {isSearchingClauses && (
        <div className="flex items-center gap-3 rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-blue-300">
          <Loader2 className="h-5 w-5 shrink-0 animate-spin text-blue-400" />
          <div className="text-sm">
            <p className="font-semibold">Retrieving regulatory clauses with semantic AI...</p>
            <p className="text-xs text-blue-300/80">
              Loading the semantic embedding model (BAAI/bge-large-en-v1.5) on cold start may take up to 60 seconds. Subsequent searches will be instant.
            </p>
          </div>
        </div>
      )}

      {/* Error state display */}
      {errorMsg && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{errorMsg}</p>
        </div>
      )}

      {/* Step 1 Results: Selectable Clauses */}
      {clauses.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-zinc-400 px-1">
            <span>Select a regulatory clause to evaluate organization compliance:</span>
            <span className="font-mono text-zinc-500">{clauses.length} clauses found</span>
          </div>

          <div className="space-y-2">
            {clauses.map((c) => {
              const isSelected = selectedClause?.clause_id === c.clause_id;
              return (
                <div
                  key={c.clause_id}
                  className={`rounded-xl border p-4 transition-all ${
                    isSelected
                      ? "border-blue-500/50 bg-blue-500/10 shadow-lg"
                      : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        {c.regulator && (
                          <span className="rounded bg-blue-500/20 px-2 py-0.5 text-[10px] font-bold text-blue-300">
                            {c.regulator}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-zinc-300">
                          {c.document_name ?? "Regulatory Document"}
                          {c.clause_number ? ` (Clause ${c.clause_number})` : ""}
                        </span>
                        <span className="font-mono text-[10px] text-emerald-400">
                          {(c.similarity * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">{c.text}</p>
                    </div>

                    <button
                      onClick={() => handleEvaluateRisk(c)}
                      disabled={!activeOrgId || isEvaluating}
                      className="shrink-0 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors"
                    >
                      {isEvaluating && isSelected ? "Evaluating..." : "Evaluate Risk"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 2 Results: Compliance Risk Assessment (real backend fields) */}
      {riskResult && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4 rounded-xl border border-white/10 bg-zinc-900/90 p-6 shadow-2xl"
        >
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Compliance Risk Assessment</h2>
                {isDemoMode && <DemoBadge />}
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Organization: <span className="font-mono text-zinc-300">{activeOrganization?.name ?? riskResult.organization_id}</span>
                {" · "}
                Status:{" "}
                <span className={`font-semibold ${
                  riskResult.compliance_status === "COMPLIANT" ? "text-emerald-400" :
                  riskResult.compliance_status === "PARTIALLY_COMPLIANT" ? "text-amber-400" : "text-red-400"
                }`}>
                  {riskResult.compliance_status.replace(/_/g, " ")}
                </span>
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-zinc-500 mb-0.5">Risk Score</div>
                <div className="text-2xl font-bold text-white">{riskResult.risk_score.toFixed(1)}<span className="text-sm text-zinc-500">/100</span></div>
              </div>
              <span className={`rounded-md border px-2.5 py-1 text-xs font-bold ${
                RISK_LEVEL_CLASSES[riskResult.risk_level] ?? "border-zinc-500/40 bg-zinc-500/20 text-zinc-300"
              }`}>
                {riskResult.risk_level}
              </span>
            </div>
          </div>

          {/* Explanation */}
          <div className="rounded-lg bg-white/5 p-4 text-xs text-zinc-300 leading-relaxed border border-white/5">
            <p className="font-semibold text-white mb-1 flex items-center gap-1.5">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              Risk Assessment Explanation
            </p>
            <p>{riskResult.explanation}</p>
          </div>

          {/* Confidence */}
          <div className="flex items-center gap-3">
            <TrendingUp className="h-4 w-4 text-blue-400" />
            <span className="text-xs text-zinc-400">Analysis Confidence:</span>
            <div className="flex-1 max-w-xs">
              <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-blue-500 transition-all"
                  style={{ width: `${(riskResult.confidence * 100).toFixed(0)}%` }}
                />
              </div>
            </div>
            <span className="text-xs font-mono text-blue-400">{(riskResult.confidence * 100).toFixed(0)}%</span>
          </div>

          {/* Factor Breakdown */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Risk Factor Breakdown
            </h3>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(riskResult.factor_breakdown).map(([key, detail]) => (
                <div key={key} className="rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs">
                  <p className="font-semibold text-zinc-200 capitalize">
                    {key.replace(/_/g, " ")}
                  </p>
                  {detail.description && (
                    <p className="text-[11px] text-zinc-400 mt-1">{detail.description}</p>
                  )}
                  <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-500">
                    <span>Weight: {(detail.weight * 100).toFixed(0)}%</span>
                    <span className="font-bold text-zinc-300">+{detail.contribution.toFixed(1)} pts</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Identified Gaps */}
          {riskResult.identified_gaps && riskResult.identified_gaps.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-amber-400" />
                Identified Compliance Gaps ({riskResult.identified_gaps.length})
              </h3>
              <div className="space-y-2">
                {riskResult.identified_gaps.map((gap, idx) => (
                  <div key={idx} className="flex items-start gap-2 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs">
                    <span className={`mt-0.5 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-bold ${
                      GAP_SEVERITY_CLASSES[gap.severity] ?? "text-zinc-400 bg-zinc-500/10 border-zinc-500/30"
                    }`}>
                      {gap.severity}
                    </span>
                    <p className="text-zinc-300 leading-relaxed">{gap.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No gaps state */}
          {riskResult.identified_gaps && riskResult.identified_gaps.length === 0 && riskResult.compliance_status === "COMPLIANT" && (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-xs text-emerald-400">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              <span>No compliance gaps identified. Organization policies are compliant with this clause.</span>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
