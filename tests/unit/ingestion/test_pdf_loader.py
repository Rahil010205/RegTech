"""Tests for PDFLoader."""

from pathlib import Path

import fitz
import pytest

from app.ingestion.pdf_loader import InvalidPDFError, PDFLoader, PDFFileNotFoundError


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Reserve Bank of India circular text")
    doc.save(pdf_path)
    doc.close()
    return pdf_path


class TestPDFLoader:
    def test_load_pdf_returns_page_records(self, sample_pdf: Path) -> None:
        loader = PDFLoader(sample_pdf)
        pages = loader.load_pdf()
        assert len(pages) == 1
        assert pages[0]["page_number"] == 1
        assert "Reserve Bank of India" in pages[0]["text"]

    def test_get_metadata(self, sample_pdf: Path) -> None:
        metadata = PDFLoader(sample_pdf).get_metadata()
        assert metadata["filename"] == "sample.pdf"
        assert metadata["total_pages"] == 1

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PDFFileNotFoundError):
            PDFLoader(tmp_path / "missing.pdf")

    def test_invalid_extension_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.txt"
        bad.write_text("not pdf", encoding="utf-8")
        with pytest.raises(InvalidPDFError):
            PDFLoader(bad)
