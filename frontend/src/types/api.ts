// ─── Regulation ──────────────────────────────────────────────────────────────

export type RegulatorCode = "RBI" | "SEBI" | "IRDAI" | "GDPR" | "ISO" | "OTHER";

export type RegulationDocumentType = "circular" | "guideline" | "act" | "policy" | "sop" | "procedure";

export type ProcessingStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface Regulation {
  id: string;
  title: string;
  regulator_code: RegulatorCode;
  document_type?: string;
  version: string;
  status: ProcessingStatus;
  clause_count: number;
  uploaded_at: string;
  uploaded_by: string;
}

export interface RegulationUploadPayload {
  file: File;
  regulator_code: RegulatorCode;
  title: string;
  document_type: string;
  version: string;
}

export interface RegulationUploadResponse {
  regulation_id: string;
  version_id: string;
  job_id: string;
  status: string;
  message: string;
}

export interface RegulationListResponse {
  items: Regulation[];
  total: number;
  skip: number;
  limit: number;
}

// ─── Policy Document ─────────────────────────────────────────────────────────

export type DocumentType = "KYC_SOP" | "AML_POLICY" | "RISK_FRAMEWORK" | "INTERNAL_AUDIT" | "OTHER";

/**
 * PolicyDocument maps to the backend DocumentResponse schema from GET /documents.
 * Fields match exactly what the backend returns.
 */
export interface PolicyDocument {
  id: string;
  /** organization UUID */
  org_id: string;
  /** source filename as uploaded */
  filename: string;
  /** document type from backend (e.g. "policy", "sop") */
  doc_type: string;
  status: string;
  /** ISO timestamp from backend */
  created_at: string;
  content_hash?: string;
}

export interface PolicyUploadPayload {
  file: File;
  title: string;
  document_type: DocumentType;
}

export interface PolicyUploadResponse {
  document_id: string;
  job_id: string;
  status: string;
  message: string;
}

export interface DocumentListResponse {
  items: PolicyDocument[];
  total: number;
  skip: number;
  limit: number;
}

// ─── Organizations ────────────────────────────────────────────────────────────

export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginatedOrganizationResponse {
  items: OrganizationResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface OrganizationCreateRequest {
  name: string;
  slug: string;
}

// ─── Compliance / Risk / Search ───────────────────────────────────────────────

/**
 * Maps to backend RetrievedClause from GET /search.
 * Actual backend fields: clause_id, document_id, document_name, regulator,
 * clause_number, section, text, page_number, similarity, metadata.
 */
export interface RegulatoryClauseResult {
  clause_id: string;
  document_id: string;
  /** regulation document name (replaces regulation_title) */
  document_name: string | null;
  /** regulator code e.g. "RBI" (replaces regulator_code) */
  regulator: string | null;
  clause_number: string | null;
  section?: string | null;
  text: string;
  similarity: number;
  metadata?: Record<string, unknown>;
}

export interface SearchRetrievalResponse {
  query: string;
  top_k: number;
  min_similarity?: number | null;
  results: RegulatoryClauseResult[];
  total_results: number;
}

// ─── Risk Scoring — matches backend RiskScoringResponse exactly ───────────────

export interface IdentifiedGap {
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface RiskFactorDetail {
  value: number;
  weight: number;
  contribution: number;
  description?: string | null;
}

export interface RiskFactorBreakdown {
  compliance_severity: RiskFactorDetail;
  regulatory_criticality: RiskFactorDetail;
  gap_severity: RiskFactorDetail;
  evidence_strength: RiskFactorDetail;
  confidence: RiskFactorDetail;
}

/**
 * Matches backend RiskScoringResponse exactly.
 * Key fields: risk_score (0-100), risk_level, explanation, factor_breakdown,
 * identified_gaps, confidence, compliance_status.
 * NOTE: No matching_evidence, overall_risk_score, reasoning, or factors fields.
 */
export interface RiskScoringResponse {
  id?: string | null;
  organization_id: string;
  regulatory_clause_id: string;
  compliance_status: "COMPLIANT" | "PARTIALLY_COMPLIANT" | "NON_COMPLIANT" | "UNKNOWN";
  /** Normalized 0–100 risk score */
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  /** Analysis confidence 0.0–1.0 */
  confidence: number;
  factor_breakdown: RiskFactorBreakdown;
  identified_gaps: IdentifiedGap[];
  /** Auditor-ready narrative explanation */
  explanation: string;
  created_at?: string | null;
}

// ─── Legacy types (kept for backwards compat; not used in new pages) ──────────

export interface RegulatoryClause {
  id: string;
  regulation_id: string;
  regulation_title: string;
  regulator_code: RegulatorCode;
  clause_number: string;
  text: string;
  similarity_score: number;
}

export interface PolicyChunkMatch {
  id: string;
  document_id: string;
  document_title: string;
  chunk_index: number;
  text: string;
  similarity_score: number;
}

export interface ComplianceGap {
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface RiskMatch {
  regulatory_clause: RegulatoryClause;
  policy_chunks: PolicyChunkMatch[];
  risk_score: number;
  compliance_status: "COMPLIANT" | "PARTIALLY_COMPLIANT" | "NON_COMPLIANT" | "UNKNOWN";
  reasoning: string;
  identified_gaps: ComplianceGap[];
}

export interface ComplianceRiskResponse {
  org_id: string;
  query: string;
  matches: RiskMatch[];
  overall_risk_score: number;
  summary: string;
  evaluated_at: string;
}

// ─── Health ──────────────────────────────────────────────────────────────────

export interface ServiceStatus {
  connected: boolean;
  error?: string | null;
}

export interface BackendHealthResponse {
  status: "ok" | "degraded";
  db: ServiceStatus;
  qdrant: ServiceStatus;
}
