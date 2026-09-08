// ─── Regulation ──────────────────────────────────────────────────────────────

export type RegulatorCode = "RBI" | "SEBI" | "IRDAI" | "GDPR" | "ISO" | "OTHER";

export type ProcessingStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface Regulation {
  id: string;
  title: string;
  regulator_code: RegulatorCode;
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
  version: string;
}

export interface RegulationUploadResponse {
  id: string;
  title: string;
  status: ProcessingStatus;
  message: string;
}

// ─── Policy Document ─────────────────────────────────────────────────────────

export type DocumentType = "KYC_SOP" | "AML_POLICY" | "RISK_FRAMEWORK" | "INTERNAL_AUDIT" | "OTHER";

export interface PolicyDocument {
  id: string;
  org_id: string;
  title: string;
  document_type: DocumentType;
  status: ProcessingStatus;
  chunk_count: number;
  uploaded_at: string;
  uploaded_by: string;
}

export interface PolicyUploadPayload {
  file: File;
  title: string;
  document_type: DocumentType;
}

export interface PolicyUploadResponse {
  id: string;
  title: string;
  status: ProcessingStatus;
  message: string;
}

// ─── Compliance / Risk ────────────────────────────────────────────────────────

export interface ComplianceRiskRequest {
  query: string;
  regulation_id?: string;
  top_k?: number;
}

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

export interface HealthStatus {
  status: "ok" | "degraded" | "down";
  version: string;
  services: {
    database: "ok" | "error";
    qdrant: "ok" | "error";
    redis: "ok" | "error";
    celery: "ok" | "error";
  };
  uptime_seconds: number;
}
