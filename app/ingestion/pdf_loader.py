"""PDF text extraction using PyMuPDF (fitz)."""

from pathlib import Path
from typing import TypedDict

import fitz
from loguru import logger


class PDFLoaderError(Exception):
    """Base exception for PDF loading failures."""


class PDFFileNotFoundError(PDFLoaderError):
    """Raised when the PDF file path does not exist."""


class InvalidPDFError(PDFLoaderError):
    """Raised when the file is not a valid PDF."""


class PDFOpenError(PDFLoaderError):
    """Raised when the PDF cannot be opened or parsed."""


class PageContent(TypedDict):
    """Raw text content extracted from a single PDF page."""

    page_number: int
    text: str


class PdfMetadata(TypedDict):
    """Basic metadata for a PDF file."""

    filename: str
    total_pages: int


class PDFLoader:
    """Load a PDF and extract raw page-wise text using PyMuPDF."""

    _PDF_MAGIC = b"%PDF"
    _PDF_SUFFIX = ".pdf"

    def __init__(self, file_path: Path | str) -> None:
        """
        Initialize the loader with a path to a PDF file.

        Args:
            file_path: Filesystem path to the PDF document.

        Raises:
            PDFFileNotFoundError: If the path does not exist or is not a file.
            InvalidPDFError: If the file does not have a PDF extension or magic header.
        """
        self.file_path = Path(file_path)
        self._logger = logger.bind(module="pdf_loader", file=str(self.file_path))
        self._validate_file_path()

    def load_pdf(self) -> list[PageContent]:
        """
        Open the PDF and extract text from every page.

        Returns:
            A list of dictionaries, one per page, each containing:
            ``{"page_number": int, "text": str}``.

        Raises:
            PDFOpenError: If the PDF cannot be opened or parsed.
        """
        self._logger.info("Loading PDF pages")

        pages: list[PageContent] = []

        try:
            with fitz.open(self.file_path) as document:
                for page in document:
                    page_number = page.number + 1
                    text = page.get_text()
                    pages.append({"page_number": page_number, "text": text})
                    self._logger.debug(
                        "Extracted page {page_number} ({char_count} chars)",
                        page_number=page_number,
                        char_count=len(text),
                    )
        except fitz.FileDataError as exc:
            self._logger.error("PDF data is corrupt or invalid: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to open PDF '{self.file_path.name}': file is corrupt or invalid."
            ) from exc
        except RuntimeError as exc:
            self._logger.error("Failed to open PDF: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to open PDF '{self.file_path.name}': {exc}"
            ) from exc
        except OSError as exc:
            self._logger.error("Filesystem error reading PDF: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to read PDF '{self.file_path.name}': {exc}"
            ) from exc

        self._logger.info(
            "Successfully loaded {page_count} pages from '{filename}'",
            page_count=len(pages),
            filename=self.file_path.name,
        )
        return pages

    def get_metadata(self) -> PdfMetadata:
        """
        Return basic metadata for the PDF.

        Returns:
            A dictionary containing ``filename`` and ``total_pages``.

        Raises:
            PDFOpenError: If the PDF cannot be opened to determine page count.
        """
        self._logger.debug("Reading PDF metadata")

        try:
            with fitz.open(self.file_path) as document:
                total_pages = document.page_count
        except fitz.FileDataError as exc:
            self._logger.error("PDF data is corrupt or invalid: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to read metadata for '{self.file_path.name}': file is corrupt or invalid."
            ) from exc
        except RuntimeError as exc:
            self._logger.error("Failed to open PDF for metadata: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to read metadata for '{self.file_path.name}': {exc}"
            ) from exc
        except OSError as exc:
            self._logger.error("Filesystem error reading PDF metadata: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to read metadata for '{self.file_path.name}': {exc}"
            ) from exc

        metadata: PdfMetadata = {
            "filename": self.file_path.name,
            "total_pages": total_pages,
        }
        self._logger.debug(
            "Metadata for '{filename}': {total_pages} pages",
            filename=metadata["filename"],
            total_pages=metadata["total_pages"],
        )
        return metadata

    def _validate_file_path(self) -> None:
        """Validate that the path exists and points to a PDF file."""
        if not self.file_path.exists():
            self._logger.error("PDF file not found: {path}", path=str(self.file_path))
            raise PDFFileNotFoundError(f"PDF file not found: '{self.file_path}'")

        if not self.file_path.is_file():
            self._logger.error("Path is not a file: {path}", path=str(self.file_path))
            raise PDFFileNotFoundError(f"Path is not a file: '{self.file_path}'")

        if self.file_path.suffix.lower() != self._PDF_SUFFIX:
            self._logger.error(
                "Invalid file extension '{suffix}' for path: {path}",
                suffix=self.file_path.suffix,
                path=str(self.file_path),
            )
            raise InvalidPDFError(
                f"File '{self.file_path.name}' is not a PDF: expected '{self._PDF_SUFFIX}' extension."
            )

        try:
            with self.file_path.open("rb") as handle:
                header = handle.read(len(self._PDF_MAGIC))
        except OSError as exc:
            self._logger.error("Unable to read file header: {error}", error=str(exc))
            raise PDFOpenError(
                f"Unable to read file '{self.file_path.name}': {exc}"
            ) from exc

        if header != self._PDF_MAGIC:
            self._logger.error(
                "Invalid PDF magic header for file: {path}",
                path=str(self.file_path),
            )
            raise InvalidPDFError(
                f"File '{self.file_path.name}' is not a valid PDF: missing PDF header."
            )
