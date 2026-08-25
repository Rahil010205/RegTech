"""Tests for MetadataExtractor."""

from app.ingestion.clause_splitter import ClauseRecord
from app.ingestion.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    def setup_method(self) -> None:
        self.extractor = MetadataExtractor()

    def test_extracts_regulator_and_date(self) -> None:
        text = """
        Reserve Bank of India
        Master Direction - Know Your Customer (KYC) Direction, 2016
        Effective from 1st January 2016
        """
        metadata = self.extractor.extract(text, "rbi_kyc.pdf")
        assert metadata["regulator"] == "RBI"
        assert metadata["document_type"] == "master direction"
        assert metadata["effective_date"] == "2016-01-01"
        assert metadata["source"] == "rbi_kyc.pdf"

    def test_does_not_hallucinate_missing_fields(self) -> None:
        metadata = self.extractor.extract("Short text only.", "unknown.pdf")
        assert metadata["publication_date"] is None
        assert metadata["version"] is None

    def test_enrich_clause_combines_document_and_clause_metadata(self) -> None:
        clause: ClauseRecord = {
            "clause_number": "4.1",
            "level": 2,
            "title": "Retention period",
            "text": "The organization shall retain customer records.",
            "parent_clause": "4",
            "section": "Section 4 — Data Retention",
            "page_number": 3,
            "page_end": 3,
        }
        doc_meta = {
            "document_name": "Data Retention Policy",
            "document_type": "regulation",
            "regulator": "RBI",
            "jurisdiction": "IN",
            "effective_date": "2016-01-01",
            "publication_date": None,
            "version": "1.0",
            "section": "Section 4",
            "source": "policy.pdf",
        }
        enriched = self.extractor.enrich_clause(clause, doc_meta, document_id="abc-123")
        assert enriched["document_id"] == "abc-123"
        assert enriched["clause_number"] == "4.1"
        assert enriched["page_number"] == 3
        assert enriched["section"] == "Section 4 — Data Retention"
