"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ShieldCheck, Sparkles, ArrowRight, X } from "lucide-react";
import { runComplianceRisk, MOCK_ORG_ID } from "@/lib/api-client";
import { ComplianceResultCard } from "@/components/ui/compliance-result-card";
import { RiskBadge } from "@/components/ui/risk-badge";
import type { ComplianceRiskResponse, RiskMatch } from "@/types/api";

// ─── Rich mock response for demo ─────────────────────────────────────────────
function buildMockResponse(query: string): ComplianceRiskResponse {
  const matches: RiskMatch[] = [
    {
      regulatory_clause: {
        id: "clause_rbi_kyc_001",
        regulation_id: "reg_001",
        regulation_title: "RBI Master Direction on KYC 2023",
        regulator_code: "RBI",
        clause_number: "16(a)",
        text: "Every Regulated Entity (RE) shall establish and implement a Customer Due Diligence (CDD) policy that encompasses risk-based categorisation of customers, continuous transaction monitoring, and periodic review of high-risk accounts at intervals not exceeding twelve months.",
        similarity_score: 0.91,
      },
      policy_chunks: [
        {
          id: "chunk_001",
          document_id: "doc_001",
          document_title: "Company KYC SOP",
          chunk_index: 4,
          text: "Section 3.2: All new customers shall be categorized as Low, Medium, or High risk based on the scoring matrix defined in Annexure A. High-risk customers shall be subject to Enhanced Due Diligence (EDD) procedures and reviewed annually.",
          similarity_score: 0.88,
        },
        {
          id: "chunk_002",
          document_id: "doc_001",
          document_title: "Company KYC SOP",
          chunk_index: 12,
          text: "Section 6.1: Transaction monitoring alerts are generated automatically by the AML system for transactions exceeding threshold limits. Relationship Managers are required to review and close alerts within 5 business days.",
          similarity_score: 0.74,
        },
      ],
      risk_score: 18,
      compliance_status: "COMPLIANT",
      reasoning:
        "The organization's KYC SOP demonstrates strong alignment with RBI's CDD requirements. Risk categorization, EDD procedures, and annual review cycles are explicitly documented. Transaction monitoring is automated with clear SLA commitments.",
      identified_gaps: [],
    },
    {
      regulatory_clause: {
        id: "clause_rbi_kyc_031",
        regulation_id: "reg_001",
        regulation_title: "RBI Master Direction on KYC 2023",
        regulator_code: "RBI",
        clause_number: "31(b)",
        text: "Regulated Entities must maintain KYC records for a minimum of eight years after the end of the business relationship. Records must be retrievable within 24 hours upon regulatory request and stored in tamper-evident format.",
        similarity_score: 0.83,
      },
      policy_chunks: [
        {
          id: "chunk_003",
          document_id: "doc_001",
          document_title: "Company KYC SOP",
          chunk_index: 18,
          text: "Section 8: Customer records shall be retained for a period of 5 years from the date of closure of account or termination of business relationship, whichever is later.",
          similarity_score: 0.69,
        },
      ],
      risk_score: 76,
      compliance_status: "NON_COMPLIANT",
      reasoning:
        "Critical gap identified: the organization's retention policy specifies 5 years while RBI mandates a minimum of 8 years. Additionally, the SOP does not address tamper-evident storage requirements or the 24-hour retrieval SLA. Immediate remediation is required.",
      identified_gaps: [
        {
          description:
            "Record retention period is 5 years in policy; RBI requires minimum 8 years.",
          severity: "CRITICAL",
        },
        {
          description: "No mention of tamper-evident storage format.",
          severity: "HIGH",
        },
        {
          description:
            "24-hour retrieval SLA upon regulatory request not documented.",
          severity: "HIGH",
        },
      ],
    },
    {
      regulatory_clause: {
        id: "clause_rbi_kyc_055",
        regulation_id: "reg_001",
        regulation_title: "RBI Master Direction on KYC 2023",
        regulator_code: "RBI",
        clause_number: "55(c)",
        text: "REs shall designate a Principal Officer (PO) responsible for KYC/AML compliance. The PO shall have direct reporting access to the Board and shall submit quarterly compliance reports.",
        similarity_score: 0.77,
      },
      policy_chunks: [
        {
          id: "chunk_004",
          document_id: "doc_002",
          document_title: "Anti-Money Laundering Policy 2024",
          chunk_index: 2,
          text: "The Chief Compliance Officer (CCO) is designated as the Principal Officer for AML/KYC purposes. The CCO reports to the Board Risk Committee on a semi-annual basis.",
          similarity_score: 0.82,
        },
      ],
      risk_score: 42,
      compliance_status: "PARTIALLY_COMPLIANT",
      reasoning:
        "A Principal Officer is designated and has Board-level access. However, the organization reports semi-annually while RBI mandates quarterly reporting. This is a moderate gap requiring process adjustment.",
      identified_gaps: [
        {
          description:
            "Reporting frequency is semi-annual; RBI mandates quarterly compliance reports to the Board.",
          severity: "MEDIUM",
        },
      ],
    },
  ];

  const overallScore = Math.round(
    matches.reduce((sum, m) => sum + m.risk_score, 0) / matches.length,
  );

  return {
    org_id: MOCK_ORG_ID,
    query,
    matches,
    overall_risk_score: overallScore,
    summary: `Analysis complete for query: "${query}". Found ${matches.length} regulatory clauses. ${matches.filter((m) => m.compliance_status === "NON_COMPLIANT").length} critical non-compliance issues require immediate attention.`,
    evaluated_at: new Date().toISOString(),
  };
}

const EXAMPLE_QUERIES = [
  "KYC customer due diligence requirements",
  "AML transaction monitoring obligations",
  "Data retention and record keeping",
  "Board reporting and governance",
  "Risk categorization and EDD procedures",
];

export default function CompliancePage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [result, setResult] = useState<ComplianceRiskResponse | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSearch = useCallback(
    async (searchQuery?: string) => {
      const q = (searchQuery ?? query).trim();
      if (!q) return;

      setQuery(q);
      setIsSearching(true);
      setHasSearched(true);

      try {
        const data = await runComplianceRisk(MOCK_ORG_ID, { query: q, top_k: 5 });
        setResult(data);
      } catch {
        // Demo fallback — always show rich results
        await new Promise((r) => setTimeout(r, 1200));
        setResult(buildMockResponse(q));
      } finally {
        setIsSearching(false);
      }
    },
    [query],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSearch();
    },
    [handleSearch],
  );

  const handleClear = useCallback(() => {
    setQuery("");
    setResult(null);
    setHasSearched(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  return (
    <div className="mx-auto max-w-4xl">
      {/* Animated search bar — centered when no results, top when results present */}
      <motion.div
        layout
        animate={hasSearched ? { marginTop: 0 } : { marginTop: "12vh" }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
        className="space-y-4"
      >
        {/* Hero header — only visible before first search */}
        <AnimatePresence>
          {!hasSearched && (
            <motion.div
              key="hero"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10, height: 0 }}
              transition={{ duration: 0.35 }}
              className="mb-8 text-center"
            >
              <div className="mb-4 flex justify-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-600/20 to-violet-600/20 shadow-2xl shadow-blue-500/10">
                  <ShieldCheck className="h-8 w-8 text-blue-400" />
                </div>
              </div>
              <h1 className="text-2xl font-bold tracking-tight lg:text-3xl">
                Compliance Search
              </h1>
              <p className="mt-2 text-zinc-500">
                Semantically search regulations and analyse your organisation&apos;s
                compliance posture with AI-powered risk scoring.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-500" />
          <input
            ref={inputRef}
            id="compliance-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about a regulation clause, obligation, or compliance topic…"
            className="w-full rounded-xl border border-white/10 bg-white/5 py-3.5 pl-12 pr-28 text-sm text-zinc-200 placeholder-zinc-600 outline-none shadow-lg backdrop-blur-sm transition-all focus:border-blue-500/50 focus:bg-white/[0.07] focus:ring-1 focus:ring-blue-500/30"
          />
          <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1">
            {(query || result) && (
              <button
                onClick={handleClear}
                className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:text-zinc-300"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <button
              id="compliance-search-btn"
              onClick={() => handleSearch()}
              disabled={!query.trim() || isSearching}
              className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-blue-500 px-3 py-1.5 text-xs font-semibold text-white shadow-md transition-all hover:from-blue-500 hover:to-blue-400 disabled:opacity-40"
            >
              {isSearching ? (
                <>
                  <Sparkles className="h-3.5 w-3.5 animate-pulse" />
                  Analysing…
                </>
              ) : (
                <>
                  Analyse
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Example queries — visible before first search */}
        <AnimatePresence>
          {!hasSearched && (
            <motion.div
              key="examples"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-wrap justify-center gap-2"
            >
              {EXAMPLE_QUERIES.map((eq) => (
                <button
                  key={eq}
                  onClick={() => handleSearch(eq)}
                  className="rounded-full border border-white/8 bg-white/[0.03] px-3 py-1.5 text-xs text-zinc-400 transition-all hover:border-white/15 hover:bg-white/[0.06] hover:text-zinc-300"
                >
                  {eq}
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Loading skeletons */}
      <AnimatePresence>
        {isSearching && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-8 space-y-3"
          >
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="glass animate-pulse rounded-xl p-5"
                style={{ animationDelay: `${i * 150}ms` }}
              >
                <div className="mb-3 flex items-center gap-2">
                  <div className="h-5 w-12 rounded-full bg-white/5" />
                  <div className="h-5 w-20 rounded-full bg-white/5" />
                  <div className="ml-auto h-5 w-16 rounded-full bg-white/5" />
                </div>
                <div className="space-y-2">
                  <div className="h-3.5 w-full rounded-full bg-white/5" />
                  <div className="h-3.5 w-4/5 rounded-full bg-white/5" />
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && !isSearching && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            className="mt-6 space-y-4"
          >
            {/* Summary bar */}
            <div className="glass flex flex-wrap items-center justify-between gap-3 rounded-xl px-4 py-3">
              <div>
                <p className="text-sm font-medium text-zinc-300">
                  {result.matches.length} clause
                  {result.matches.length !== 1 ? "s" : ""} analysed
                </p>
                <p className="text-xs text-zinc-600">{result.summary}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-zinc-600">Overall Risk</span>
                <RiskBadge
                  score={result.overall_risk_score}
                  size="md"
                  showLabel
                />
              </div>
            </div>

            {/* Result cards */}
            <div className="space-y-3">
              {result.matches.map((match, i) => (
                <ComplianceResultCard key={match.regulatory_clause.id} match={match} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
