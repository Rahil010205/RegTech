import axios from "axios";
import { useAuthStore } from "@/store/auth-store";
import type {
  Regulation,
  RegulatorCode,
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

/** Dedicated client for semantic-search calls — model load can take ~60 s on cold start. */
export const searchApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120_000,
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

// Mirror interceptors on the search client
searchApiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

searchApiClient.interceptors.response.use(
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
  const res = await apiClient.get<Record<string, unknown>>("/regulations", {
    params: { skip, limit },
  });
  const data = res.data;
  const rawItems = Array.isArray(data?.items)
    ? data.items
    : Array.isArray(data)
    ? (data as unknown[])
    : [];
  const items: Regulation[] = rawItems.map((raw: unknown) => {
    const item = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
    const currentVersion = item.current_version && typeof item.current_version === "object"
      ? (item.current_version as Record<string, unknown>)
      : null;
    const version = (currentVersion?.version || item.version || "1.0") as string;
    const rawStatus = (currentVersion?.status || item.status || "PENDING") as string;
    return {
      id: String(item.id || ""),
      title: String(item.title || ""),
      regulator_code: (item.regulator_code as RegulatorCode) || "OTHER",
      document_type: (item.document_type as Regulation["document_type"]) || "policy",
      version,
      status: rawStatus.toUpperCase() as Regulation["status"],
      clause_count: typeof item.clause_count === "number" ? item.clause_count : 0,
      uploaded_at: String(item.created_at || item.uploaded_at || ""),
      uploaded_by: String(item.uploaded_by || "Compliance Officer"),
    };
  });
  return {
    items,
    total: typeof data?.total === "number" ? data.total : items.length,
    skip: typeof data?.skip === "number" ? data.skip : skip,
    limit: typeof data?.limit === "number" ? data.limit : limit,
  };
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
  const res = await apiClient.get<DocumentListResponse>(`/organizations/${orgId}/documents`, {
    params: { skip: 0, limit: 50 },
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
  // Ensure the filename preserves or appends the .pdf extension
  const rawTitle = (payload.title || payload.file.name).trim();
  const filename = rawTitle.toLowerCase().endsWith(".pdf")
    ? rawTitle
    : `${rawTitle}.pdf`;
  const fileType = payload.file.type || "application/pdf";
  const renamedFile = new File([payload.file], filename, {
    type: fileType,
  });
  form.append("file", renamedFile);
  form.append("document_type", payload.document_type);

  const res = await apiClient.post<PolicyUploadResponse>(
    `/organizations/${orgId}/documents`,
    form,
    {
      // Embedding model cold-start (BAAI/bge-large-en-v1.5) can take 2–3 min on first upload.
      // Override the default 60 s apiClient timeout to avoid false failures.
      timeout: 180_000,
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
  // Uses searchApiClient (120 s timeout) — model load on cold start can take ~60 s.
  const res = await searchApiClient.post<SearchRetrievalResponse>("/search", {
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

// ─── Regulation Status Polling ────────────────────────────────────────────────

export interface RegulationStatusResponse {
  regulation_id: string;
  version_id: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  clause_count: number;
}

export async function getRegulationStatus(
  regulationId: string,
): Promise<RegulationStatusResponse> {
  const res = await apiClient.get<RegulationStatusResponse>(
    `/regulations/${regulationId}/status`,
  );
  return res.data;
}

