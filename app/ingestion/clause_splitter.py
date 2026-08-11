"""Clause detection and splitting for regulatory documents.

Identifies hierarchical clause numbering patterns common in RBI Master
Directions and similar regulatory documents (e.g. 1, 1.1, 1.1.1, 2.3.4)
and splits the document text into structured clause units.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TypedDict

logger = logging.getLogger(__name__)


class ClauseRecord(TypedDict):
    """A single structured clause extracted from a regulatory document."""

    clause_number: str     # e.g. "3.1.2"
    level: int             # depth: 1 → top-level, 2 → sub-clause, 3 → sub-sub-clause
    title: str             # first line / inline title if present, else ""
    text: str              # full clause body text (trimmed)
    parent_clause: str     # parent clause number, "" for top-level clauses


# ---------------------------------------------------------------------------
# Numbering pattern — matches: 1  /  1.1  /  1.1.1  /  1.1.1.1
# Must start at beginning of a line (after optional whitespace).
# ---------------------------------------------------------------------------
_CLAUSE_PATTERN = re.compile(
    r"""
    ^                           # start of line
    [ \t]*                      # optional leading whitespace
    (?P<number>
        \d+                     # primary: 1, 2, 3 …
        (?:\.\d+){0,3}          # optional sub-levels: .1  .2  .3
    )
    (?P<sep>[.\s])              # separator after number: dot or space
    [ \t]*                      # optional space
    (?P<rest>.*)                # rest of the line (may be clause title)
    $
    """,
    re.VERBOSE | re.MULTILINE,
)

# Minimum characters a clause body must have to be kept
_MIN_CLAUSE_LENGTH = 10


@dataclass
class _ClauseCandidate:
    number: str
    level: int
    title: str
    lines: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        combined = " ".join(line.strip() for line in self.lines if line.strip())
        return combined.strip()

    @property
    def parent_clause(self) -> str:
        parts = self.number.rsplit(".", 1)
        return parts[0] if len(parts) > 1 else ""


class ClauseSplitter:
    """Split cleaned document text into structured regulatory clause units.

    How it works:
        1. Scan every line for the ``_CLAUSE_PATTERN`` regex.
        2. When a clause heading is found, flush the previous candidate.
        3. Lines between headings become the clause body.
        4. Short fragments (< ``_MIN_CLAUSE_LENGTH`` chars) are discarded.

    Why regex (not ML):
        Regulatory clause numbers follow strict typographic conventions.
        Regex is deterministic, fast, and produces auditable splits.
    """

    def split(self, text: str) -> list[ClauseRecord]:
        """Split *text* into a list of :class:`ClauseRecord` dicts.

        Args:
            text: Cleaned full-document text (from ``TextCleaner.clean_document``).

        Returns:
            Ordered list of clause dicts.  Returns ``[]`` for blank input.
        """
        if not text or not text.strip():
            logger.warning("ClauseSplitter received empty text")
            return []

        lines = text.splitlines()
        candidates: list[_ClauseCandidate] = []
        current: _ClauseCandidate | None = None
        preamble_lines: list[str] = []

        for line in lines:
            match = _CLAUSE_PATTERN.match(line)

            if match:
                # Flush previous candidate
                if current is not None:
                    candidates.append(current)
                else:
                    # Preamble text before the first numbered clause
                    preamble_text = " ".join(preamble_lines).strip()
                    if len(preamble_text) >= _MIN_CLAUSE_LENGTH:
                        candidates.append(
                            _ClauseCandidate(
                                number="0",
                                level=0,
                                title="Preamble",
                                lines=preamble_lines[:],
                            )
                        )

                number = match.group("number")
                rest = match.group("rest").strip()
                level = number.count(".") + 1

                current = _ClauseCandidate(
                    number=number,
                    level=level,
                    title=rest,
                    lines=[rest] if rest else [],
                )
            else:
                stripped = line.strip()
                if current is not None:
                    current.lines.append(stripped)
                else:
                    preamble_lines.append(stripped)

        # Flush the last candidate
        if current is not None:
            candidates.append(current)

        # Convert to ClauseRecord dicts, discarding empty/tiny fragments
        records: list[ClauseRecord] = []
        for cand in candidates:
            body = cand.text
            if len(body) < _MIN_CLAUSE_LENGTH and not cand.title:
                logger.debug("Skipping short clause fragment: %s", cand.number)
                continue
            records.append(
                ClauseRecord(
                    clause_number=cand.number,
                    level=cand.level,
                    title=cand.title,
                    text=body,
                    parent_clause=cand.parent_clause,
                )
            )

        logger.info("ClauseSplitter produced %d clause records", len(records))
        return records
