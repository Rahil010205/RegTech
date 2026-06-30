"""PDF parser port."""

from pathlib import Path
from typing import Protocol


class PdfParserPort(Protocol):
  """Abstract interface for PDF text extraction."""

  def extract_text(self, file_path: Path) -> str:
    """Extract raw text from a PDF file."""
    ...

  def extract_pages(self, file_path: Path) -> list[str]:
    """Extract text per page from a PDF file."""
    ...
