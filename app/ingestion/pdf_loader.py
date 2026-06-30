"""PDF loader — orchestrates PyMuPDF, pdfplumber, and Unstructured fallback chain."""

from pathlib import Path


class PdfLoader:
  """Extract text from PDF using a fallback chain of parsers."""

  def load(self, file_path: Path) -> str:
    """Load and return full document text. Implementation pending."""
    raise NotImplementedError

  def load_pages(self, file_path: Path) -> list[str]:
    """Load and return per-page text. Implementation pending."""
    raise NotImplementedError
