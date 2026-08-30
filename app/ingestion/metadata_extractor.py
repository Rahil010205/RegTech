"""Metadata extraction from regulatory documents."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from loguru import logger

from app.ingestion.clause_splitter import ClauseRecord

_REGULATOR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("RBI", re.compile(r"\bReserve\s+Bank\s+of\s+India\b|\bRBI\b", re.IGNORECASE)),
    ("SEBI", re.compile(r"\bSEBI\b|\bSecurities\s+and\s+Exchange\s+Board", re.IGNORECASE)),
    ("IRDAI", re.compile(r"\bIRDAI\b|\bInsurance\s+Regulatory", re.IGNORECASE)),
    ("GDPR", re.compile(r"\bGDPR\b|\bGeneral\s+Data\s+Protection\s+Regulation", re.IGNORECASE)),
    ("ISO", re.compile(r"\bISO\b|\bInternational\s+Organization\s+for\s+Standardization", re.IGNORECASE)),
    ("PCI_DSS", re.compile(r"\bPCI[\s-]?DSS\b", re.IGNORECASE)),
]

_JURISDICTION_BY_REGULATOR = {
    "RBI": "IN",
    "SEBI": "IN",
    "IRDAI": "IN",
    "GDPR": "EU",
    "ISO": "GLOBAL",
    "PCI_DSS": "GLOBAL",
}

_DOC_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("master direction", re.compile(r"master\s+direction", re.IGNORECASE)),
    ("circular", re.compile(r"\bcircular\b", re.IGNORECASE)),
    ("guideline", re.compile(r"\bguideline[s]?\b", re.IGNORECASE)),
    ("notification", re.compile(r"\bnotification\b", re.IGNORECASE)),
    ("act", re.compile(r"\bact\b", re.IGNORECASE)),
    ("policy", re.compile(r"\bpolic(?:y|ies)\b", re.IGNORECASE)),
]

_MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


class MetadataExtractor:
    """Extract document- and clause-level metadata without hallucination."""

    _SCAN_CHARS = 5_000

    def extract(self, text: str, filename: str) -> dict[str, Any]:
        """Extract document-level metadata from cleaned text and filename."""
        scan_region = text[: self._SCAN_CHARS]
        regulator = self._extract_regulator(scan_region) or self._extract_regulator(filename)
        doc_type = self._extract_doc_type(scan_region, filename)
        doc_name = self._extract_document_name(text, filename)

        metadata = {
            "document_name": doc_name or None,
            "document_type": doc_type or None,
            "regulator": regulator or None,
            "jurisdiction": _JURISDICTION_BY_REGULATOR.get(regulator) if regulator else None,
            "effective_date": self._extract_effective_date(text) or None,
            "publication_date": self._extract_publication_date(text) or None,
            "version": self._extract_version(text, filename) or None,
            "section": self._extract_section(scan_region) or None,
            "subsection": None,
            "source": filename,
            "filename": filename,
            "total_pages": None,
        }
        logger.info(
            "Metadata extracted — regulator={} type={} date={}",
            metadata["regulator"],
            metadata["document_type"],
            metadata["effective_date"],
        )
        return metadata

    def enrich_clause(
        self,
        clause: ClauseRecord,
        document_metadata: dict[str, Any],
        *,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """Attach document metadata to an individual clause record."""
        clause_num = clause["clause_number"]
        parent = clause.get("parent_clause") or ""
        
        section_number = None
        sub_clause = None
        
        if re.match(r"^\d+(?:\.\d+)*$", clause_num):
            section_number = clause_num
        elif re.match(r"^\([a-zA-Z0-9]+\)$", clause_num):
            if parent and re.match(r"^\d+(?:\.\d+)*$", parent):
                section_number = parent
                sub_clause = f"{parent}{clause_num}"
            else:
                sub_clause = clause_num

        return {
            "document_id": document_id,
            "document_name": document_metadata.get("document_name"),
            "document_type": document_metadata.get("document_type"),
            "regulator": document_metadata.get("regulator") or "RBI",
            "jurisdiction": document_metadata.get("jurisdiction"),
            "effective_date": document_metadata.get("effective_date"),
            "publication_date": document_metadata.get("publication_date"),
            "version": document_metadata.get("version"),
            "section": clause.get("section") or document_metadata.get("section"),
            "subsection": clause.get("parent_clause") or None,
            "clause_number": clause_num,
            "page_number": clause.get("page_number"),
            "page_end": clause.get("page_end"),
            "source": document_metadata.get("source"),
            "title": clause.get("title") or None,
            "level": clause.get("level"),
            "parent_clause": clause.get("parent_clause") or None,
            "chapter": clause.get("section") or document_metadata.get("section") or None,
            "section_number": section_number,
            "sub_clause": sub_clause,
            "source_type": "regulatory_document",
        }

    def parse_effective_date(self, value: str | None) -> date | None:
        """Convert ISO-like date strings to ``date`` objects."""
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _extract_regulator(self, text: str) -> str:
        for name, pattern in _REGULATOR_PATTERNS:
            if pattern.search(text):
                return name
        return ""

    def _extract_doc_type(self, text: str, filename: str) -> str:
        combined = text[:2000] + " " + filename
        for doc_type, pattern in _DOC_TYPE_PATTERNS:
            if pattern.search(combined):
                return doc_type
        return ""

    def _extract_document_name(self, text: str, filename: str) -> str:
        non_empty = [line.strip() for line in text.splitlines() if line.strip()][:15]
        for line in non_empty:
            if re.search(
                r"master\s+direction|circular|guideline|notification|regulation",
                line,
                re.IGNORECASE,
            ):
                return line[:200]
            if len(line) > 20 and line[0].isupper() and not re.match(r"^\d", line):
                return line[:200]
        stem = Path(filename).stem.replace("_", " ").replace("-", " ")
        return stem.title()

    def _extract_effective_date(self, text: str) -> str:
        return self._find_first_date(text)

    def _extract_publication_date(self, text: str) -> str:
        publication_match = re.search(
            r"(?:published|issued|publication\s+date)\s*[:\-]?\s*"
            r"((?:\d{1,2}(?:st|nd|rd|th)?\s+\w+\s+\d{4})|\d{4}-\d{2}-\d{2})",
            text[:8000],
            re.IGNORECASE,
        )
        if publication_match:
            return self._normalize_date_string(publication_match.group(1))
        return ""

    def _extract_version(self, text: str, filename: str) -> str:
        version_match = re.search(
            r"(?:version|ver\.?)\s*[:\-]?\s*([A-Za-z0-9._-]+)",
            text[:5000],
            re.IGNORECASE,
        )
        if version_match:
            return version_match.group(1)
        filename_match = re.search(r"v(\d+(?:\.\d+)*)", filename, re.IGNORECASE)
        if filename_match:
            return filename_match.group(1)
        return ""

    def _extract_section(self, text: str) -> str:
        match = re.search(
            r"(?:section|article|rule|chapter)\s+(\d+[A-Za-z]?(?:\.[A-Za-z0-9]+)*)"
            r"[:\-—]?\s*(.{0,80})",
            text,
            re.IGNORECASE,
        )
        if match:
            title = match.group(2).strip()
            prefix = match.group(0).split(":")[0].strip()
            return f"{prefix} — {title}" if title else prefix
        return ""

    def _find_first_date(self, text: str) -> str:
        match = re.search(
            r"(\d{1,2})(?:st|nd|rd|th)?\s+"
            r"(January|February|March|April|May|June|July|August|September|"
            r"October|November|December),?\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if match:
            day, month_name, year = match.group(1), match.group(2).lower(), match.group(3)
            month = _MONTHS.get(month_name, "01")
            return f"{year}-{month}-{int(day):02d}"

        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match:
            return match.group(0)

        match = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", text)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        return ""

    def _normalize_date_string(self, raw: str) -> str:
        cleaned = raw.strip()
        iso_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", cleaned)
        if iso_match:
            return cleaned
        return self._find_first_date(cleaned)
