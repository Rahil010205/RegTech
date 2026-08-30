"""Clause detection and splitting for regulatory documents.

Identifies hierarchical clause numbering patterns common in regulatory
documents (numeric, alphabetic, roman, Section/Article/Rule headers) and
splits document text into structured, retrieval-ready clause units.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TypedDict

from loguru import logger

from app.ingestion.pdf_loader import PageContent


class ClauseRecord(TypedDict):
    """A single structured clause extracted from a regulatory document."""

    clause_number: str
    level: int
    title: str
    text: str
    parent_clause: str
    section: str
    page_number: int | None
    page_end: int | None


@dataclass
class _AnnotatedLine:
    page_number: int
    text: str


@dataclass
class _ClauseCandidate:
    number: str
    level: int
    title: str
    section: str
    lines: list[_AnnotatedLine] = field(default_factory=list)

    @property
    def text(self) -> str:
        combined = " ".join(line.text.strip() for line in self.lines if line.text.strip())
        return combined.strip()

    @property
    def parent_clause(self) -> str:
        if re.match(r"^\([a-z]+\)$", self.number):
            return self.section or ""
        if re.match(r"^\([ivxlc]+\)$", self.number, re.IGNORECASE):
            parts = self.number
            return parts
        parts = self.number.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""

    @property
    def page_number(self) -> int | None:
        if not self.lines:
            return None
        return self.lines[0].page_number

    @property
    def page_end(self) -> int | None:
        if not self.lines:
            return None
        return self.lines[-1].page_number


class ClauseSplitter:
    """Split cleaned regulatory text into meaningful compliance units.

    Supported heading patterns:
        - Numeric: 1, 1.1, 1.1.1
        - Alphabetic: (a), (b)
        - Roman: (i), (ii)
        - Structural: Section 1, Article 2, Rule 3, Chapter 4

    Section headers update context but do not create standalone tiny clauses
    unless they carry substantive body text.
    """

    _NUMERIC_CLAUSE = re.compile(
        r"^[ \t]*(?P<number>\d+(?:\.\d+){0,3})[.\s][ \t]*(?P<rest>.+)$"
    )
    _NUM_SUB_CLAUSE = re.compile(r"^[ \t]*\((?P<label>\d+)\)[ \t]+(?P<rest>.+)$")
    _ALPHA_CLAUSE = re.compile(r"^[ \t]*\((?P<label>[a-z])\)[ \t]+(?P<rest>.+)$", re.IGNORECASE)
    _ROMAN_CLAUSE = re.compile(
        r"^[ \t]*\((?P<label>[ivxlc]+)\)[ \t]+(?P<rest>.+)$",
        re.IGNORECASE,
    )
    _STRUCTURAL_HEADER = re.compile(
        r"^[ \t]*(?:Section|Article|Rule|Chapter)\s+"
        r"(?P<number>[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)"
        r"[ \t]*[:\-—]?\s*(?P<rest>.*)$",
    )

    _STANDALONE_NUMERIC = re.compile(r"^\d+(?:\.\d+){0,3}\.?$")
    _STANDALONE_PAREN_NUM = re.compile(r"^\(\d+\)$")
    _STANDALONE_PAREN_ALPHA = re.compile(r"^\([a-z]\)$", re.IGNORECASE)
    _STANDALONE_PAREN_ROMAN = re.compile(r"^\([ivxlc]+\)$", re.IGNORECASE)

    _MIN_CLAUSE_LENGTH = 10

    def split(self, text: str) -> list[ClauseRecord]:
        """Split merged document text into clause records."""
        if not text or not text.strip():
            logger.warning("ClauseSplitter received empty text")
            return []

        annotated = [
            _AnnotatedLine(page_number=1, text=line)
            for line in text.splitlines()
        ]
        return self._split_annotated_lines(annotated)

    def split_pages(self, pages: list[PageContent]) -> list[ClauseRecord]:
        """Split page-wise cleaned content while preserving page numbers."""
        annotated: list[_AnnotatedLine] = []
        for page in pages:
            page_number = page["page_number"]
            for line in page["text"].splitlines():
                annotated.append(_AnnotatedLine(page_number=page_number, text=line))
        return self._split_annotated_lines(annotated)

    def _preprocess_lines(self, lines: list[_AnnotatedLine]) -> list[_AnnotatedLine]:
        preprocessed: list[_AnnotatedLine] = []
        i = 0
        n = len(lines)
        while i < n:
            curr_line = lines[i]
            stripped = curr_line.text.strip()
            
            is_standalone = (
                self._STANDALONE_NUMERIC.match(stripped) or
                self._STANDALONE_PAREN_NUM.match(stripped) or
                self._STANDALONE_PAREN_ALPHA.match(stripped) or
                self._STANDALONE_PAREN_ROMAN.match(stripped)
            )
            
            if is_standalone and i + 1 < n:
                j = i + 1
                while j < n and not lines[j].text.strip():
                    j += 1
                if j < n:
                    next_line = lines[j]
                    merged_text = f"{stripped} {next_line.text.strip()}"
                    preprocessed.append(_AnnotatedLine(page_number=curr_line.page_number, text=merged_text))
                    i = j + 1
                    continue
            
            preprocessed.append(curr_line)
            i += 1
        return preprocessed

    def _split_annotated_lines(self, lines: list[_AnnotatedLine]) -> list[ClauseRecord]:
        merged_lines = self._preprocess_lines(lines)
        
        candidates: list[_ClauseCandidate] = []
        current: _ClauseCandidate | None = None
        current_section = ""
        preamble_lines: list[_AnnotatedLine] = []
        current_numeric_parent = ""
        current_sub_parent = ""
        current_alpha_parent = ""

        for annotated in merged_lines:
            raw = annotated.text
            stripped = raw.strip()
            if not stripped:
                if current is not None:
                    current.lines.append(annotated)
                else:
                    preamble_lines.append(annotated)
                continue

            structural = self._STRUCTURAL_HEADER.match(stripped)
            if structural:
                if current is not None:
                    candidates.append(current)
                    current = None
                keyword = structural.group(0).split()[0]
                section_number = structural.group("number")
                section_title = structural.group("rest").strip()
                current_section = (
                    f"{keyword} {section_number}"
                    + (f" — {section_title}" if section_title else "")
                ).strip()
                if keyword.lower() != "chapter" and section_title and len(section_title) >= self._MIN_CLAUSE_LENGTH:
                    current = _ClauseCandidate(
                        number=section_number,
                        level=1,
                        title=section_title,
                        section=current_section,
                        lines=[annotated],
                    )
                continue

            numeric = self._NUMERIC_CLAUSE.match(stripped)
            numeric_sub = self._NUM_SUB_CLAUSE.match(stripped)
            alpha = self._ALPHA_CLAUSE.match(stripped)
            roman = self._ROMAN_CLAUSE.match(stripped)

            if numeric:
                if current is not None:
                    candidates.append(current)
                elif preamble_lines:
                    self._append_preamble(candidates, preamble_lines)
                    preamble_lines = []

                number = numeric.group("number")
                rest = numeric.group("rest").strip()
                current_numeric_parent = number
                current_sub_parent = number
                current_alpha_parent = number
                current = _ClauseCandidate(
                    number=number,
                    level=number.count(".") + 1,
                    title=rest,
                    section=current_section,
                    lines=[_AnnotatedLine(annotated.page_number, rest)] if rest else [],
                )
                continue

            if numeric_sub:
                if current is not None:
                    candidates.append(current)
                label = numeric_sub.group("label")
                rest = numeric_sub.group("rest").strip()
                sub_number = f"{current_numeric_parent}({label})" if current_numeric_parent else f"({label})"
                current_sub_parent = sub_number
                current_alpha_parent = sub_number
                current = _ClauseCandidate(
                    number=sub_number,
                    level=(current_numeric_parent.count(".") + 2 if current_numeric_parent else 2),
                    title=rest,
                    section=current_section,
                    lines=[_AnnotatedLine(annotated.page_number, rest)] if rest else [],
                )
                continue

            if alpha:
                if current is not None:
                    candidates.append(current)
                label = alpha.group("label").lower()
                rest = alpha.group("rest").strip()
                alpha_number = f"{current_sub_parent}({label})" if current_sub_parent else f"({label})"
                current_alpha_parent = alpha_number
                current = _ClauseCandidate(
                    number=alpha_number,
                    level=(current_numeric_parent.count(".") + 2 if current_numeric_parent else 2),
                    title=rest,
                    section=current_section,
                    lines=[_AnnotatedLine(annotated.page_number, rest)] if rest else [],
                )
                continue

            if roman:
                if current is not None:
                    candidates.append(current)
                label = roman.group("label").lower()
                rest = roman.group("rest").strip()
                roman_number = f"{current_alpha_parent}({label})" if current_alpha_parent else f"({label})"
                current = _ClauseCandidate(
                    number=roman_number,
                    level=(current_numeric_parent.count(".") + 3 if current_numeric_parent else 3),
                    title=rest,
                    section=current_section,
                    lines=[_AnnotatedLine(annotated.page_number, rest)] if rest else [],
                )
                continue

            if current is not None:
                current.lines.append(annotated)
            else:
                preamble_lines.append(annotated)

        if current is not None:
            candidates.append(current)
        elif preamble_lines:
            self._append_preamble(candidates, preamble_lines)

        return self._finalize_candidates(candidates)

    def _append_preamble(
        self,
        candidates: list[_ClauseCandidate],
        preamble_lines: list[_AnnotatedLine],
    ) -> None:
        preamble_text = " ".join(line.text.strip() for line in preamble_lines if line.text.strip())
        if len(preamble_text) >= self._MIN_CLAUSE_LENGTH:
            candidates.append(
                _ClauseCandidate(
                    number="0",
                    level=0,
                    title="Preamble",
                    section="",
                    lines=preamble_lines,
                )
            )

    def _finalize_candidates(self, candidates: list[_ClauseCandidate]) -> list[ClauseRecord]:
        records: list[ClauseRecord] = []
        for candidate in candidates:
            body = candidate.text
            if len(body) < self._MIN_CLAUSE_LENGTH and not candidate.title:
                logger.debug("Skipping short clause fragment: {}", candidate.number)
                continue
            records.append(
                ClauseRecord(
                    clause_number=candidate.number,
                    level=candidate.level,
                    title=candidate.title,
                    text=body,
                    parent_clause=candidate.parent_clause,
                    section=candidate.section,
                    page_number=candidate.page_number,
                    page_end=candidate.page_end,
                )
            )
        logger.info("ClauseSplitter produced {} clause records", len(records))
        return records
