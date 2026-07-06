"""Unit tests for TextCleaner."""

import pytest

from app.ingestion.pdf_loader import PageContent
from app.ingestion.text_cleaner import (
    EmptyTextError,
    TextCleaner,
    TextCleanerConfig,
    TextCleaningError,
)


@pytest.fixture
def cleaner() -> TextCleaner:
    return TextCleaner()


class TestCleanSingleBlock:
    def test_fixes_end_of_line_hyphenation(self, cleaner: TextCleaner) -> None:
        raw = "The institu-\ntion shall maintain records."
        result = cleaner.clean(raw)
        assert result == "The institution shall maintain records."

    def test_removes_soft_hyphen(self, cleaner: TextCleaner) -> None:
        raw = "regu\u00adlation"
        result = cleaner.clean(raw)
        assert result == "regulation"

    def test_removes_page_number_lines(self, cleaner: TextCleaner) -> None:
        raw = "Reserve Bank of India\n12\nSection 3.1\nPage 12 of 40"
        result = cleaner.clean(raw)
        assert "12" not in result.splitlines()
        assert "Page 12 of 40" not in result
        assert "Section 3.1" in result

    def test_normalizes_whitespace(self, cleaner: TextCleaner) -> None:
        raw = "Clause   4.2\t\trequires   reporting.\n\n\n\nNext paragraph."
        result = cleaner.clean(raw)
        assert "Clause 4.2 requires reporting." in result
        assert "\n\nNext paragraph." in result

    def test_empty_input_allowed_by_default(self, cleaner: TextCleaner) -> None:
        assert cleaner.clean("   ") == ""

    def test_raises_on_empty_when_configured(self) -> None:
        cleaner = TextCleaner(TextCleanerConfig(raise_on_empty=True))
        with pytest.raises(EmptyTextError):
            cleaner.clean("   ")

    def test_raises_on_none_input(self, cleaner: TextCleaner) -> None:
        with pytest.raises(TextCleaningError):
            cleaner.clean(None)  # type: ignore[arg-type]


class TestCleanPages:
    def test_removes_repeated_headers_and_footers(self) -> None:
        pages: list[PageContent] = [
            {
                "page_number": 1,
                "text": "RBI/2024-25/100\nSection 1\nBody text page one.\nwww.rbi.org.in",
            },
            {
                "page_number": 2,
                "text": "RBI/2024-25/100\nSection 2\nBody text page two.\nwww.rbi.org.in",
            },
            {
                "page_number": 3,
                "text": "RBI/2024-25/100\nSection 3\nBody text page three.\nwww.rbi.org.in",
            },
        ]

        cleaner = TextCleaner()
        cleaned = cleaner.clean_pages(pages)

        assert len(cleaned) == 3
        assert all("RBI/2024-25/100" not in page["text"] for page in cleaned)
        assert all("www.rbi.org.in" not in page["text"] for page in cleaned)
        assert "Body text page one." in cleaned[0]["text"]
        assert cleaned[0]["page_number"] == 1

    def test_returns_empty_list_for_empty_input(self, cleaner: TextCleaner) -> None:
        assert cleaner.clean_pages([]) == []

    def test_clean_document_joins_pages(self, cleaner: TextCleaner) -> None:
        pages: list[PageContent] = [
            {"page_number": 1, "text": "Chapter 1 content."},
            {"page_number": 2, "text": "Chapter 2 content."},
        ]
        document = cleaner.clean_document(pages)
        assert document == "Chapter 1 content.\n\nChapter 2 content."

    def test_header_detection_skipped_for_single_page(self) -> None:
        pages: list[PageContent] = [
            {"page_number": 1, "text": "Repeated Header\nMain content.\nRepeated Footer"},
        ]
        cleaner = TextCleaner()
        cleaned = cleaner.clean_pages(pages)
        assert "Repeated Header" in cleaned[0]["text"]


class TestConfiguration:
    def test_can_disable_page_number_removal(self) -> None:
        cleaner = TextCleaner(TextCleanerConfig(remove_page_numbers=False))
        raw = "Content\n42\nMore content"
        result = cleaner.clean(raw)
        assert "42" in result.splitlines()

    def test_can_disable_broken_word_fix(self) -> None:
        cleaner = TextCleaner(TextCleanerConfig(fix_broken_words=False))
        raw = "institu-\ntion"
        result = cleaner.clean(raw)
        assert "institu-" in result or "institu-\n" in result
