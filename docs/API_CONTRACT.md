# OpenAPI Endpoint Contract
# Base URL: /api/v1
# Auth: Bearer JWT (future) — currently optional in dev mode

## Health

| Method | Path | Request | Response 200 |
|--------|------|---------|--------------|
| GET | /health | — | `{ "message": "ok" }` |
| GET | /health/ready | — | `{ "message": "ready" }` |

## Auth (Future)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | /auth/login | `{ "email", "password" }` | 501 Not Implemented |
| POST | /auth/refresh | `{ "refresh_token" }` | 501 Not Implemented |

## Regulations

| Method | Path | Request | Response 202/200 |
|--------|------|---------|------------------|
| POST | /regulations/upload | multipart: `file`, `regulator_code`, `title`, `document_type`, `version` | `RegulationUploadResponse` |
| GET | /regulations | query: `skip`, `limit` | `RegulationListResponse` |
| GET | /regulations/{regulation_id} | — | `RegulationResponse` |

### RegulationUploadResponse
```json
{
  "regulation_id": "uuid",
  "version_id": "uuid",
  "job_id": "uuid",
  "status": "pending",
  "message": "string"
}
```

## Documents

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | /documents/upload | multipart: `file`, `org_id`, `doc_type` | `DocumentUploadResponse` |
| GET | /documents | query: `org_id`, `skip`, `limit` | `DocumentListResponse` |
| GET | /documents/{document_id} | — | `DocumentDetailResponse` |

## Compliance

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | /compliance/evaluate | `ComplianceEvaluateRequest` | `ComplianceEvaluateResponse` |
| GET | /compliance/runs/{run_id} | — | `ComplianceRunDetailResponse` |
| GET | /compliance/runs/{run_id}/findings | — | `ComplianceFindingsListResponse` |

### ComplianceEvaluateRequest
```json
{
  "org_id": "uuid",
  "document_id": "uuid",
  "regulator_codes": ["RBI", "SEBI"],
  "regulation_version_ids": null
}
```

## Reports

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | /reports/generate | `{ "run_id", "format": "json|pdf" }` | `ReportGenerateResponse` |
| GET | /reports/{report_id} | — | `ReportResponse` |

## Error Response (all endpoints)

```json
{
  "error_code": "NOT_FOUND",
  "message": "Regulation 'uuid' not found",
  "details": {},
  "request_id": "uuid"
}
```
