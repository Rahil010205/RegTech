"""Text cleaning and normalization for regulatory PDF extraction output."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import TypedDict

from loguru import logger

from app.ingestion.pdf_loader import PageContent


class TextCleaningError(Exception):
    """Base exception for text cleaning failures."""


class EmptyTextError(TextCleaningError):
    """Raised when input text is empty and empty input is not permitted."""


class CleanedPageContent(TypedDict):
    """Cleaned text content for a single PDF page."""

    page_number: int
    text: str


@dataclass(frozen=True)
class TextCleanerConfig:
    """
    Configuration for regulatory document text normalization.

    Attributes:
        remove_page_numbers: Strip standalone page-number lines from each page.
        remove_headers_footers: Detect and remove repeated header/footer lines.
        normalize_whitespace: Collapse redundant spaces and normalize line breaks.
        fix_broken_words: Rejoin words split by end-of-line hyphenation.
        header_footer_scan_lines: Number of top/bottom lines scanned per page.
        header_footer_min_ratio: Minimum cross-page frequency to classify as header/footer.
        min_pages_for_header_detection: Minimum pages required before header/footer detection.
        preserve_paragraph_breaks: Keep blank lines between paragraphs after normalization.
        raise_on_empty: Raise ``EmptyTextError`` when input is blank.
    """

    remove_page_numbers: bool = True
    remove_headers_footers: bool = True
    normalize_whitespace: bool = True
    fix_broken_words: bool = True
    header_footer_scan_lines: int = 3
    header_footer_min_ratio: float = 0.6
    min_pages_for_header_detection: int = 2
    preserve_paragraph_breaks: bool = True
    raise_on_empty: bool = False


class TextCleaner:
    """
    Normalize raw PDF text extracted by ``PDFLoader``.

    Why this class exists:
        PyMuPDF returns faithful text including repeating headers, footers, page
        numbers, and line-break hyphenation. Downstream ``ClauseSplitter`` and
        ``MetadataExtractor`` require stable, clause-friendly text. This class
        isolates all normalization rules in one testable, configurable component.

    Why regex (not spaCy) here:
        Cleaning is deterministic structural normalization. Regex is faster,
        predictable, and does not require model downloads at import time.
        spaCy is reserved for semantic clause detection in ``clause_splitter``.
    """

    _PAGE_NUMBER_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"^\s*\d+\s*$"),
        re.compile(r"^\s*-\s*\d+\s*-\s*$"),
        re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
        re.compile(r"^\s*page\s+\d+(\s+of\s+\d+)?\s*$", re.IGNORECASE),
        re.compile(r"^\s*\[\s*\d+\s*\]\s*$"),
    )

    _SOFT_HYPHEN = "\u00ad"
    _BROKEN_WORD_PATTERN = re.compile(r"(\w)-(?:\s*\n\s*|\s+)(\w)", re.UNICODE)
    _MULTI_SPACE_PATTERN = re.compile(r"[^\S\n]+")
    _EXCESS_NEWLINES_PATTERN = re.compile(r"\n{3,}")

    def __init__(self, config: TextCleanerConfig | None = None) -> None:
        """
        Initialize the cleaner.

        Args:
            config: Optional configuration. Defaults are tuned for regulatory PDFs.
        """
        self.config = config or TextCleanerConfig()
        self._logger = logger.bind(module="text_cleaner")

    def clean(self, text: str) -> str:
        """
        Clean a single text block (one page or merged document fragment).

        Applies page-number removal, broken-word repair, and whitespace
        normalization. Does not perform cross-page header/footer detection;
        use ``clean_pages`` for multi-page documents.

        Args:
            text: Raw extracted text.

        Returns:
            Normalized text.

        Raises:
            EmptyTextError: If ``raise_on_empty`` is enabled and input is blank.
        """
        self._validate_input(text)

        original_length = len(text)
        cleaned = text.replace(self._SOFT_HYPHEN, "")

        if self.config.fix_broken_words:
            cleaned = self._fix_broken_words(cleaned)

        if self.config.remove_page_numbers:
            cleaned = self._remove_page_numbers(cleaned)

        if self.config.normalize_whitespace:
            cleaned = self._normalize_whitespace(cleaned)

        self._logger.debug(
            "Cleaned text block: {original} -> {cleaned} chars",
            original=original_length,
            cleaned=len(cleaned),
        )
        return cleaned

    def clean_pages(self, pages: list[PageContent]) -> list[CleanedPageContent]:
        """
        Clean page-wise text from ``PDFLoader.load_pdf()``.

        Performs cross-page header/footer detection when enough pages are
        available, then applies per-page normalization.

        Args:
            pages: List of ``{"page_number": int, "text": str}`` from PDFLoader.

        Returns:
            Same structure with normalized ``text`` values.

        Raises:
            EmptyTextError: If ``raise_on_empty`` is enabled and all pages are blank.
        """
        if not pages:
            self._logger.warning("Received empty page list for cleaning")
            return []

        if self.config.raise_on_empty and all(not page["text"].strip() for page in pages):
            raise EmptyTextError("All pages contain empty text.")

        header_lines: set[str] = set()
        footer_lines: set[str] = set()

        if (
            self.config.remove_headers_footers
            and len(pages) >= self.config.min_pages_for_header_detection
        ):
            header_lines, footer_lines = self._detect_repeated_boundary_lines(pages)
            self._logger.info(
                "Detected {header_count} header and {footer_count} footer line(s)",
                header_count=len(header_lines),
                footer_count=len(footer_lines),
            )

        cleaned_pages: list[CleanedPageContent] = []

        for page in pages:
            page_text = page["text"]

            if header_lines or footer_lines:
                page_text = self._strip_boundary_lines(
                    page_text,
                    header_lines=header_lines,
                    footer_lines=footer_lines,
                )

            cleaned_text = self.clean(page_text)
            cleaned_pages.append(
                {
                    "page_number": page["page_number"],
                    "text": cleaned_text,
                }
            )

        self._logger.info(
            "Cleaned {page_count} page(s)",
            page_count=len(cleaned_pages),
        )
        return cleaned_pages

    def clean_document(self, pages: list[PageContent]) -> str:
        """
        Clean all pages and merge into a single document string.

        Used when downstream modules (e.g. clause splitter) operate on full
        document text while preserving page order.

        Args:
            pages: Page-wise content from PDFLoader.

        Returns:
            Single normalized string with pages separated by double newlines.
        """
        cleaned_pages = self.clean_pages(pages)
        return "\n\n".join(page["text"] for page in cleaned_pages if page["text"])

    def _validate_input(self, text: str) -> None:
        if text is None:
            raise TextCleaningError("Input text cannot be None.")
        if self.config.raise_on_empty and not text.strip():
            raise EmptyTextError("Input text is empty.")

    def _fix_broken_words(self, text: str) -> str:
        """Rejoin words broken by end-of-line or inline hyphenation."""
        previous = None
        current = text

        while previous != current:
            previous = current
            current = self._BROKEN_WORD_PATTERN.sub(r"\1\2", current)

        return current

    def _remove_page_numbers(self, text: str) -> str:
        """Remove lines that contain only page-number patterns."""
        kept_lines: list[str] = []

        for line in text.splitlines():
            if any(pattern.match(line) for pattern in self._PAGE_NUMBER_PATTERNS):
                self._logger.debug("Removed page-number line: {line}", line=line.strip())
                continue
            kept_lines.append(line)

        return "\n".join(kept_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize spaces, tabs, and paragraph breaks."""
        normalized_lines: list[str] = []

        for line in text.splitlines():
            stripped = self._MULTI_SPACE_PATTERN.sub(" ", line.strip())
            normalized_lines.append(stripped)

        normalized = "\n".join(normalized_lines).strip()

        if self.config.preserve_paragraph_breaks:
            normalized = self._EXCESS_NEWLINES_PATTERN.sub("\n\n", normalized)
        else:
            normalized = re.sub(r"\n+", " ", normalized)
            normalized = self._MULTI_SPACE_PATTERN.sub(" ", normalized).strip()

        return normalized

    def _detect_repeated_boundary_lines(
        self,
        pages: list[PageContent],
    ) -> tuple[set[str], set[str]]:
        """
        Identify header/footer lines repeated across multiple pages.

        Regulatory PDFs typically repeat authority name, circular number, and
        page numbers in the same positions on every page.
        """
        scan_lines = self.config.header_footer_scan_lines
        page_count = len(pages)
        threshold = max(2, int(page_count * self.config.header_footer_min_ratio))

        header_counter: Counter[str] = Counter()
        footer_counter: Counter[str] = Counter()

        for page in pages:
            lines = [line.strip() for line in page["text"].splitlines() if line.strip()]
            if not lines:
                continue

            for line in lines[:scan_lines]:
                header_counter[self._normalize_line_for_comparison(line)] += 1

            for line in lines[-scan_lines:]:
                footer_counter[self._normalize_line_for_comparison(line)] += 1

        header_lines = {
            line for line, count in header_counter.items() if count >= threshold and line
        }
        footer_lines = {
            line for line, count in footer_counter.items() if count >= threshold and line
        }

        return header_lines, footer_lines

    def _strip_boundary_lines(
        self,
        text: str,
        *,
        header_lines: set[str],
        footer_lines: set[str],
    ) -> str:
        """Remove detected header and footer lines from a single page."""
        kept_lines: list[str] = []

        for line in text.splitlines():
            normalized = self._normalize_line_for_comparison(line)
            if normalized in header_lines or normalized in footer_lines:
                self._logger.debug("Removed boundary line: {line}", line=line.strip())
                continue
            kept_lines.append(line)

        return "\n".join(kept_lines)

    @staticmethod
    def _normalize_line_for_comparison(line: str) -> str:
        """
        Normalize a line for cross-page frequency comparison.

        Only case-folds and collapses whitespace so structurally different
        lines (e.g. "Chapter 1" vs "Chapter 2") are not merged incorrectly.
        """
        return re.sub(r"\s+", " ", line.strip().lower())
