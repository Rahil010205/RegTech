"""Tests for ClauseSplitter."""

from app.ingestion.clause_splitter import ClauseSplitter


class TestClauseSplitter:
    def setup_method(self) -> None:
        self.splitter = ClauseSplitter()

    def test_splits_numeric_hierarchy(self) -> None:
        text = """
        1. General Provisions
        All regulated entities must comply.

        1.1 Scope
        This section applies to all banks.

        1.2 Definitions
        Customer means any account holder.
        """
        records = self.splitter.split(text)
        numbers = [record["clause_number"] for record in records]
        assert "1" in numbers
        assert "1.1" in numbers
        assert "1.2" in numbers
        assert all(len(record["text"]) >= 10 for record in records)

    def test_splits_section_example_from_spec(self) -> None:
        text = """
        Section 4 — Data Retention

        4.1 The organization shall retain customer records for a minimum period of seven years.

        4.2 Records must be protected against unauthorized modification.
        """
        records = self.splitter.split(text)
        numbers = [record["clause_number"] for record in records]
        assert "4.1" in numbers
        assert "4.2" in numbers
        clause_41 = next(record for record in records if record["clause_number"] == "4.1")
        assert "seven years" in clause_41["text"]
        assert "Data Retention" in (clause_41["section"] or "")

    def test_splits_alpha_subclauses(self) -> None:
        text = """
        2. Requirements
        Each institution must implement controls.

        (a) Maintain audit logs for all access events.
        (b) Review logs at least quarterly.
        """
        records = self.splitter.split(text)
        labels = [record["clause_number"] for record in records]
        assert "2" in labels
        assert "2(a)" in labels
        assert "2(b)" in labels

    def test_split_pages_preserves_page_numbers(self) -> None:
        pages = [
            {"page_number": 1, "text": "1. Intro\nApplies to all entities."},
            {"page_number": 2, "text": "1.1 Scope\nThis continues on page two."},
        ]
        records = self.splitter.split_pages(pages)
        intro = next(record for record in records if record["clause_number"] == "1")
        scope = next(record for record in records if record["clause_number"] == "1.1")
        assert intro["page_number"] == 1
        assert scope["page_number"] == 2
        assert scope["page_end"] == 2

    def test_does_not_create_tiny_fragments(self) -> None:
        text = "1. OK\nValid clause with enough regulatory content to pass threshold."
        records = self.splitter.split(text)
        assert len(records) == 1
        assert len(records[0]["text"]) >= 10

    def test_merges_standalone_numbering_lines(self) -> None:
        text = """
        Chapter III — Customer Acceptance Policy
        16.
        The NBFC shall frame a Customer Acceptance Policy.
        17.
        Without prejudice to the generality...
        (1)
        not open any account in an anonymous name.
        """
        records = self.splitter.split(text)
        numbers = [record["clause_number"] for record in records]
        assert "16" in numbers
        assert "17" in numbers
        assert "17(1)" in numbers
        c16 = next(r for r in records if r["clause_number"] == "16")
        assert c16["text"] == "The NBFC shall frame a Customer Acceptance Policy."
