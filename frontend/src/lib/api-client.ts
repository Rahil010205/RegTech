import axios from "axios";
import { useAuthStore } from "@/store/auth-store";
import type {
  RegulationUploadPayload,
  RegulationUploadResponse,
  RegulationListResponse,
  DocumentListResponse,
  PolicyUploadPayload,
  PolicyUploadResponse,
  BackendHealthResponse,
  OrganizationResponse,
  PaginatedOrganizationResponse,
  OrganizationCreateRequest,
  SearchRetrievalResponse,
  RiskScoringResponse,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  },
);

// ─── Regulations ─────────────────────────────────────────────────────────────

export async function listRegulations(
  skip = 0,
  limit = 50,
): Promise<RegulationListResponse> {
  const res = await apiClient.get<RegulationListResponse>("/regulations", {
    params: { skip, limit },
  });
  return res.data;
}

export async function uploadRegulation(
  payload: RegulationUploadPayload,
  onUploadProgress?: (percent: number) => void,
): Promise<RegulationUploadResponse> {
  const form = new FormData();
  form.append("file", payload.file);
  form.append("regulator_code", payload.regulator_code);
  form.append("title", payload.title);
  form.append("document_type", payload.document_type || "policy");
  form.append("version", payload.version);

  const res = await apiClient.post<RegulationUploadResponse>(
    "/regulations/upload",
    form,
    {
      onUploadProgress: (event) => {
        if (event.total && onUploadProgress) {
          onUploadProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return res.data;
}

// ─── Organization Documents ───────────────────────────────────────────────────

/**
 * List policy documents for an organization.
 * Calls GET /documents?org_id={orgId} (the documents router).
 */
export async function listOrgDocuments(orgId: string): Promise<DocumentListResponse> {
  const res = await apiClient.get<DocumentListResponse>("/documents", {
    params: { org_id: orgId },
  });
  return res.data;
}

/**
 * Upload a policy document for an organization.
 * Calls POST /organizations/{orgId}/documents.
 * Note: title is sent as part of the filename; document_type is required.
 */
export async function uploadOrgDocument(
  orgId: string,
  payload: PolicyUploadPayload,
  onUploadProgress?: (percent: number) => void,
): Promise<PolicyUploadResponse> {
  const form = new FormData();
  // Rename file to use title as filename so the backend stores it sensibly
  const renamedFile = new File([payload.file], payload.title || payload.file.name, {
    type: payload.file.type,
  });
  form.append("file", renamedFile);
  form.append("document_type", payload.document_type);

  const res = await apiClient.post<PolicyUploadResponse>(
    `/organizations/${orgId}/documents`,
    form,
    {
      onUploadProgress: (event) => {
        if (event.total && onUploadProgress) {
          onUploadProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return res.data;
}

// ─── Compliance / Search / Risk ───────────────────────────────────────────────

/**
 * Search regulatory clauses by semantic similarity.
 * Calls POST /search with { query, top_k }.
 * Returns SearchRetrievalResponse with results: RetrievedClause[].
 */
export async function searchRegulatoryClauses(
  query: string,
  top_k = 10,
): Promise<SearchRetrievalResponse> {
  const res = await apiClient.post<SearchRetrievalResponse>("/search", {
    query,
    top_k,
  });
  return res.data;
}

/**
 * Evaluate compliance risk for an organization against a regulatory clause.
 * Calls POST /organizations/{orgId}/compliance/risk.
 * Returns RiskScoringResponse with risk_score, explanation, factor_breakdown, etc.
 */
export async function evaluateComplianceRisk(
  orgId: string,
  regulatoryClauseId: string,
  topK = 5,
  similarityThreshold = 0.5,
): Promise<RiskScoringResponse> {
  const res = await apiClient.post<RiskScoringResponse>(
    `/organizations/${orgId}/compliance/risk`,
    {
      regulatory_clause_id: regulatoryClauseId,
      top_k: topK,
      similarity_threshold: similarityThreshold,
    },
  );
  return res.data;
}

export async function matchRegulatoryClause(
  orgId: string,
  regulatoryClauseId: string,
  topK = 5,
  similarityThreshold = 0.5,
) {
  const res = await apiClient.post(
    `/organizations/${orgId}/compliance/match`,
    {
      regulatory_clause_id: regulatoryClauseId,
      top_k: topK,
      similarity_threshold: similarityThreshold,
    },
  );
  return res.data;
}

export async function analyzeCompliance(
  orgId: string,
  regulatoryClauseId: string,
  topK = 5,
  similarityThreshold = 0.5,
) {
  const res = await apiClient.post(
    `/organizations/${orgId}/compliance/analyze`,
    {
      regulatory_clause_id: regulatoryClauseId,
      top_k: topK,
      similarity_threshold: similarityThreshold,
    },
  );
  return res.data;
}

// ─── Organizations ────────────────────────────────────────────────────────

export async function listOrganizations(
  skip = 0,
  limit = 20,
): Promise<PaginatedOrganizationResponse> {
  const res = await apiClient.get<PaginatedOrganizationResponse>("/organizations", {
    params: { skip, limit },
  });
  return res.data;
}

export async function createOrganization(
  payload: OrganizationCreateRequest,
): Promise<OrganizationResponse> {
  const res = await apiClient.post<OrganizationResponse>("/organizations", payload);
  return res.data;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<BackendHealthResponse> {
  const res = await apiClient.get<BackendHealthResponse>("/health/ready");
  return res.data;
}
