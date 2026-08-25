"""Retrieval evaluation metrics for small labeled query sets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class RetrievalEvalCase:
    """Single labeled retrieval query."""

    query: str
    expected_text_snippets: tuple[str, ...]
    unexpected_text_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalEvalResult:
    """Per-query evaluation outcome."""

    query: str
    hit_at_1: bool
    hit_at_3: bool
    hit_at_5: bool
    reciprocal_rank: float
    top_text: str


def _rank_of_match(results: Sequence[str], snippets: Iterable[str]) -> int | None:
    lowered = [text.lower() for text in results]
    for rank, text in enumerate(lowered, start=1):
        if any(snippet.lower() in text for snippet in snippets):
            return rank
    return None


def evaluate_case(case: RetrievalEvalCase, result_texts: Sequence[str]) -> RetrievalEvalResult:
    """Compute Hit@K and reciprocal rank for one query."""
    rank = _rank_of_match(result_texts, case.expected_text_snippets)
    reciprocal_rank = 1.0 / rank if rank is not None else 0.0
    top_text = result_texts[0] if result_texts else ""

    return RetrievalEvalResult(
        query=case.query,
        hit_at_1=rank is not None and rank <= 1,
        hit_at_3=rank is not None and rank <= 3,
        hit_at_5=rank is not None and rank <= 5,
        reciprocal_rank=reciprocal_rank,
        top_text=top_text,
    )


def summarize_results(results: Sequence[RetrievalEvalResult]) -> dict[str, float]:
    """Aggregate Hit@K and MRR across evaluation cases."""
    if not results:
        return {"hit_at_1": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr": 0.0}

    total = len(results)
    return {
        "hit_at_1": sum(1 for result in results if result.hit_at_1) / total,
        "hit_at_3": sum(1 for result in results if result.hit_at_3) / total,
        "hit_at_5": sum(1 for result in results if result.hit_at_5) / total,
        "mrr": sum(result.reciprocal_rank for result in results) / total,
    }
