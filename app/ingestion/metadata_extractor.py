"""Metadata extraction from regulatory documents.

Extracts structured metadata fields (Regulator, Document name, Chapter,
Section, Clause Number, Effective Date, Page Number) from document text
and filename using regex heuristics tuned for RBI regulatory documents.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)


class DocumentMetadata(TypedDict, total=False):
    """Metadata fields extracted per regulatory document."""

    regulator: str          # e.g. "RBI", "SEBI"
    document_name: str      # e.g. "Master Direction - KYC"
    document_type: str      # "circular" | "guideline" | "master direction" | …
    chapter: str            # Chapter title / number
    section: str            # Section title
    effective_date: str     # ISO-8601 date string, if found
    filename: str           # Source filename
    total_pages: int | None


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_REGULATOR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("RBI",   re.compile(r"\bReserve\s+Bank\s+of\s+India\b|\bRBI\b", re.IGNORECASE)),
    ("SEBI",  re.compile(r"\bSEBI\b|\bSecurities\s+and\s+Exchange\s+Board", re.IGNORECASE)),
    ("IRDAI", re.compile(r"\bIRDAI\b|\bInsurance\s+Regulatory", re.IGNORECASE)),
    ("GDPR",  re.compile(r"\bGDPR\b|\bGeneral\s+Data\s+Protection\s+Regulation", re.IGNORECASE)),
    ("SEBI",  re.compile(r"\bSEBI\b", re.IGNORECASE)),
]

_DOC_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("master direction", re.compile(r"master\s+direction", re.IGNORECASE)),
    ("circular",         re.compile(r"\bcircular\b", re.IGNORECASE)),
    ("guideline",        re.compile(r"\bguideline[s]?\b", re.IGNORECASE)),
    ("notification",     re.compile(r"\bnotification\b", re.IGNORECASE)),
    ("act",              re.compile(r"\bact\b", re.IGNORECASE)),
    ("policy",           re.compile(r"\bpolic(?:y|ies)\b", re.IGNORECASE)),
]

_CHAPTER_PATTERNS = [
    re.compile(r"(?:chapter|chap\.?)\s+([IVXLC\d]+[:\.\-]?\s*.{0,80})", re.IGNORECASE),
    re.compile(r"^([A-Z][A-Z\s]{4,60})$", re.MULTILINE),  # ALL-CAPS title line
]

_SECTION_PATTERNS = [
    re.compile(r"(?:section|sect\.?)\s+(\d+[A-Za-z]?[:\.\-]?\s*.{0,80})", re.IGNORECASE),
    re.compile(r"^(\d+\.\s+[A-Z][^\n]{4,80})$", re.MULTILINE),  # "3. Customer Due Diligence"
]

# Date patterns for common formats in RBI documents
_DATE_PATTERNS = [
    re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|"
               r"August|September|October|November|December),?\s+(\d{4})", re.IGNORECASE),
    re.compile(r"(January|February|March|April|May|June|July|August|September|"
               r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})", re.IGNORECASE),
    re.compile(r"(\d{2})[./-](\d{2})[./-](\d{4})"),
    re.compile(r"(\d{4})[./-](\d{2})[./-](\d{2})"),
]

_MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def _extract_regulator(text: str) -> str:
    """Return the first regulator name found, or empty string."""
    for name, pattern in _REGULATOR_PATTERNS:
        if pattern.search(text):
            return name
    return ""


def _extract_doc_type(text: str, filename: str) -> str:
    """Identify document type from text or filename."""
    combined = text[:2000] + " " + filename
    for doc_type, pattern in _DOC_TYPE_PATTERNS:
        if pattern.search(combined):
            return doc_type
    return ""


def _extract_document_name(text: str, filename: str) -> str:
    """Extract a document title from the first non-blank lines or filename."""
    # Try first 10 non-empty lines for a title-like line
    non_empty = [ln.strip() for ln in text.splitlines() if ln.strip()][:15]
    for line in non_empty:
        # Typical RBI doc title: "Master Direction – Know Your Customer (KYC) Direction, 2016"
        if re.search(r"master\s+direction|circular|guideline|notification", line, re.IGNORECASE):
            return line[:200]
        if len(line) > 20 and line[0].isupper() and not re.match(r"^\d", line):
            # Looks like a title
            return line[:200]
    # Fall back to filename (stem, cleaned up)
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    return stem.title()


def _extract_effective_date(text: str) -> str:
    """Find the first recognisable date in the document text."""
    # Named-month day year: "1st January 2016" or "January 1, 2016"
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|"
        r"August|September|October|November|December),?\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        day, month_name, year = m.group(1), m.group(2).lower(), m.group(3)
        month = _MONTHS.get(month_name, "01")
        return f"{year}-{month}-{int(day):02d}"

    m = re.search(
        r"(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
        text,
        re.IGNORECASE,
    )
    if m:
        month_name, day, year = m.group(1).lower(), m.group(2), m.group(3)
        month = _MONTHS.get(month_name, "01")
        return f"{year}-{month}-{int(day):02d}"

    # Numeric: DD/MM/YYYY or YYYY-MM-DD
    m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", text)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    return ""


def _extract_chapter(text: str) -> str:
    """Find the first chapter reference in text."""
    for pattern in _CHAPTER_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1).strip()[:120]
    return ""


def _extract_section(text: str) -> str:
    """Find the first section reference in text."""
    for pattern in _SECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1).strip()[:120]
    return ""


class MetadataExtractor:
    """Extract document-level metadata from regulatory document text.

    Operates on the first ~5,000 characters of the full document (the most
    information-dense region) plus the filename.
    """

    _SCAN_CHARS = 5_000  # Chars of document text to search for metadata

    def extract(self, text: str, filename: str) -> DocumentMetadata:
        """Return a populated :class:`DocumentMetadata` dict.

        Args:
            text:     Full cleaned document text (all pages merged).
            filename: Source PDF filename (used as fallback for doc name/type).

        Returns:
            Dict with as many fields populated as could be found.  Missing
            fields are left as empty strings rather than ``None`` so consumers
            can use ``bool(meta["effective_date"])`` checks safely.
        """
        scan_region = text[: self._SCAN_CHARS]
        regulator = _extract_regulator(scan_region) or _extract_regulator(filename)
        doc_type = _extract_doc_type(scan_region, filename)
        doc_name = _extract_document_name(text, filename)
        chapter = _extract_chapter(scan_region)
        section = _extract_section(scan_region)
        effective_date = _extract_effective_date(text)

        meta = DocumentMetadata(
            regulator=regulator,
            document_name=doc_name,
            document_type=doc_type,
            chapter=chapter,
            section=section,
            effective_date=effective_date,
            filename=filename,
            total_pages=None,  # populated by pipeline from PDFLoader.get_metadata()
        )

        logger.info(
            "Metadata extracted — regulator=%s type=%s date=%s",
            regulator or "?",
            doc_type or "?",
            effective_date or "?",
        )
        return meta
