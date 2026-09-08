import axios from "axios";
import { useAuthStore } from "@/store/auth-store";
import type {
  Regulation,
  RegulationUploadPayload,
  RegulationUploadResponse,
  PolicyDocument,
  PolicyUploadPayload,
  PolicyUploadResponse,
  ComplianceRiskRequest,
  ComplianceRiskResponse,
  HealthStatus,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const MOCK_ORG_ID = "6ae68228-4e58-4f6b-afd7-719f6d0eee78";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
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

export async function listRegulations(): Promise<Regulation[]> {
  const res = await apiClient.get<Regulation[]>("/regulations");
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
  form.append("version", payload.version);

  const res = await apiClient.post<RegulationUploadResponse>(
    "/regulations/upload",
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
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

export async function listOrgDocuments(orgId: string): Promise<PolicyDocument[]> {
  const res = await apiClient.get<PolicyDocument[]>(
    `/organizations/${orgId}/documents`,
  );
  return res.data;
}

export async function uploadOrgDocument(
  orgId: string,
  payload: PolicyUploadPayload,
  onUploadProgress?: (percent: number) => void,
): Promise<PolicyUploadResponse> {
  const form = new FormData();
  form.append("file", payload.file);
  form.append("title", payload.title);
  form.append("document_type", payload.document_type);

  const res = await apiClient.post<PolicyUploadResponse>(
    `/organizations/${orgId}/documents`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (event) => {
        if (event.total && onUploadProgress) {
          onUploadProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    },
  );
  return res.data;
}

// ─── Compliance / Risk ────────────────────────────────────────────────────────

export async function runComplianceRisk(
  orgId: string,
  request: ComplianceRiskRequest,
): Promise<ComplianceRiskResponse> {
  const res = await apiClient.post<ComplianceRiskResponse>(
    `/organizations/${orgId}/compliance/risk`,
    request,
  );
  return res.data;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await apiClient.get<HealthStatus>("/health/ready");
  return res.data;
}
