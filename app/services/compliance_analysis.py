"""LLM-based compliance analysis service (Step 2B)."""

from __future__ import annotations

import time
from uuid import UUID

from loguru import logger

from app.api.schemas.compliance_analysis import (
    ComplianceAnalysisResponse,
    ComplianceAnalysisResult,
    EvidenceReference,
)
from app.api.schemas.matching import RegulatoryPolicyMatchResponse
from app.core.config import Settings, get_settings
from app.services.llm.client import LLMClient, get_llm_client
from app.services.llm.compliance_analyzer import (
    COMPLIANCE_ANALYSIS_PROMPT_VERSION,
    LLMComplianceAnalyzer,
)
from app.services.regulatory_policy_matching import RegulatoryPolicyMatchingService


class ComplianceAnalysisService:
    """Evaluates regulatory compliance of organization policies using LLM.

    Reuses Step 2A RegulatoryPolicyMatchingService to retrieve pgvector policy
    evidence, and passes evidence to an LLM analyzer to produce a compliance
    determination with structured reasoning, gaps, and evidence references.
    """

    def __init__(
        self,
        matching_service: RegulatoryPolicyMatchingService,
        *,
        settings: Settings | None = None,
        llm_client: LLMClient | None = None,
        analyzer: LLMComplianceAnalyzer | None = None,
    ) -> None:
        self.matching_service = matching_service
        self.settings = settings or get_settings()
        self.llm_client = llm_client or get_llm_client(self.settings)
        self.analyzer = analyzer or LLMComplianceAnalyzer(self.llm_client)

    def analyze(
        self,
        organization_id: UUID,
        regulatory_clause_id: UUID,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> ComplianceAnalysisResponse:
        """Execute Step 2B LLM-based compliance analysis.

        Args:
            organization_id: Organization UUID.
            regulatory_clause_id: Regulatory clause UUID.
            top_k: Number of policy chunks to retrieve (1-50).
            similarity_threshold: Similarity score cutoff (0.0-1.0).

        Returns:
            ComplianceAnalysisResponse with compliance status, confidence, reasoning,
            evidence references, and gaps.
        """
        start_time = time.perf_counter()

        # 1. Invoke Step 2A semantic matching (handles param, org, and clause validation)
        match_response: RegulatoryPolicyMatchResponse = (
            self.matching_service.match_regulatory_clause_to_policy(
                organization_id=organization_id,
                regulatory_clause_id=regulatory_clause_id,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )
        )

        effective_top_k = match_response.top_k
        effective_threshold = match_response.similarity_threshold
        num_evidence = match_response.total_results

        # 2. Minimum Evidence Requirement:
        # If no evidence chunks retrieved above threshold, return INSUFFICIENT_EVIDENCE immediately
        # without calling the LLM.
        if num_evidence == 0:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Compliance analysis completed (no evidence) organization_id={} "
                "regulatory_clause_id={} evidence_chunks=0 threshold={} top_k={} "
                "prompt_version={} compliance_status=INSUFFICIENT_EVIDENCE confidence=0.0 latency_ms={}",
                organization_id,
                regulatory_clause_id,
                effective_threshold,
                effective_top_k,
                self.analyzer.prompt_version,
                latency_ms,
            )
            return ComplianceAnalysisResponse(
                organization_id=organization_id,
                regulatory_clause_id=regulatory_clause_id,
                compliance_status="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                reasoning=(
                    "No sufficiently relevant organization policy evidence was found "
                    "for this regulatory requirement."
                ),
                evidence=[],
                gaps=["No relevant organization policy evidence was retrieved."],
            )

        # 3. Format inputs for structured prompt
        reg_clause = match_response.regulatory_clause
        regulatory_dict = {
            "clause_id": str(reg_clause.id),
            "clause_reference": reg_clause.reference or "N/A",
            "clause_text": reg_clause.content,
            "section_title": reg_clause.section or "N/A",
            "regulation_name": reg_clause.regulation_name or "N/A",
            "regulator": reg_clause.regulator or "N/A",
            "regulation_version": reg_clause.version or "N/A",
            "effective_date": (
                reg_clause.effective_date.isoformat()
                if reg_clause.effective_date
                else "N/A"
            ),
        }

        evidence_dict_list: list[dict[str, Any]] = []
        # Mapping to validate LLM evidence references
        valid_chunks_map: dict[UUID, Any] = {}
        for hit in match_response.results:
            valid_chunks_map[hit.chunk_id] = hit
            evidence_dict_list.append({
                "chunk_id": str(hit.chunk_id),
                "document_id": str(hit.document_id),
                "document_name": hit.document_name,
                "document_type": hit.document_type,
                "document_version": hit.document_version,
                "section_title": hit.section_title or "N/A",
                "clause_reference": hit.clause_reference or "N/A",
                "similarity": hit.similarity,
                "content": hit.content,
            })

        # 4. Invoke LLM Compliance Analyzer
        analysis_result: ComplianceAnalysisResult = self.analyzer.analyze(
            regulatory_clause=regulatory_dict,
            matched_policy_chunks=evidence_dict_list,
        )

        # 5. Validate Evidence References against actual retrieved chunks
        validated_evidence: list[EvidenceReference] = []
        for ref in analysis_result.evidence:
            if ref.chunk_id in valid_chunks_map:
                actual_hit = valid_chunks_map[ref.chunk_id]
                # Enforce truth from Step 2A retrieval for document_id and similarity
                validated_evidence.append(
                    EvidenceReference(
                        chunk_id=ref.chunk_id,
                        document_id=actual_hit.document_id,
                        similarity=actual_hit.similarity,
                        relevance=ref.relevance,
                        explanation=ref.explanation,
                    )
                )
            else:
                logger.warning(
                    "Discarded invalid/hallucinated chunk_id from LLM response: {}",
                    ref.chunk_id,
                )

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        model_name = getattr(self.llm_client, "model", self.settings.llm_model)

        logger.info(
            "Compliance analysis completed organization_id={} regulatory_clause_id={} "
            "evidence_chunks={} threshold={} top_k={} llm_model={} prompt_version={} "
            "compliance_status={} confidence={} latency_ms={}",
            organization_id,
            regulatory_clause_id,
            num_evidence,
            effective_threshold,
            effective_top_k,
            model_name,
            self.analyzer.prompt_version,
            analysis_result.compliance_status,
            analysis_result.confidence,
            latency_ms,
        )

        return ComplianceAnalysisResponse(
            organization_id=organization_id,
            regulatory_clause_id=regulatory_clause_id,
            compliance_status=analysis_result.compliance_status,
            confidence=analysis_result.confidence,
            reasoning=analysis_result.reasoning,
            evidence=validated_evidence,
            gaps=analysis_result.gaps,
        )
