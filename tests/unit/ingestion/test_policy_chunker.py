"""Tests for organization policy chunking."""

from __future__ import annotations

from app.ingestion.policy_chunker import PolicyChunker


def test_policy_chunker_preserves_sections_and_clause_numbers() -> None:
    pages = [
        {
            "page_number": 1,
            "text": (
                "Section 4 — Customer Identification\n"
                "1. The regulated entity shall obtain official identification documents.\n"
                "2. The regulated entity shall verify identity before onboarding.\n"
                "3. The regulated entity shall maintain records of verification.\n"
            ),
        }
    ]
    chunks = PolicyChunker().chunk_pages(pages, document_type="KYC_POLICY")

    assert chunks
    assert all(chunk.content.strip() for chunk in chunks)
    assert any(chunk.section_title and "Customer Identification" in chunk.section_title for chunk in chunks)
    references = {chunk.clause_reference for chunk in chunks if chunk.clause_reference}
    assert "1" in references
    assert "2" in references
    assert chunks[0].metadata["document_type"] == "KYC_POLICY"


def test_policy_chunker_merges_duplicate_clause_identifiers() -> None:
    pages = [
        {
            "page_number": 1,
            "text": (
                "4.1 The organization shall conduct customer due diligence.\n"
                "Continued on the next line for the same requirement.\n"
            ),
        },
        {
            "page_number": 2,
            "text": "4.1 The organization shall also retain supporting documents.\n",
        },
    ]
    chunks = PolicyChunker().chunk_pages(pages)
    matching = [chunk for chunk in chunks if chunk.clause_reference == "4.1"]
    assert len(matching) == 1
    assert "customer due diligence" in matching[0].content.lower()
    assert "supporting documents" in matching[0].content.lower()
    assert matching[0].page_number == 1
    assert matching[0].page_end == 2
