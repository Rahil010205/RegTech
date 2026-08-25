"""Unit tests for retrieval evaluation metrics."""

from __future__ import annotations

from tests.evaluation.retrieval_metrics import RetrievalEvalCase, evaluate_case, summarize_results


def test_evaluate_case_hit_at_k() -> None:
    case = RetrievalEvalCase(
        query="retention",
        expected_text_snippets=("seven years",),
    )
    result = evaluate_case(
        case,
        [
            "Unrelated clause about capital markets.",
            "The organization shall retain customer records for seven years.",
        ],
    )
    assert result.hit_at_1 is False
    assert result.hit_at_3 is True
    assert result.reciprocal_rank == 0.5


def test_summarize_results() -> None:
    case = RetrievalEvalCase(query="q", expected_text_snippets=("match",))
    first = evaluate_case(case, ["match"])
    second = evaluate_case(case, ["miss", "match"])
    summary = summarize_results([first, second])
    assert summary["hit_at_1"] == 0.5
    assert summary["hit_at_3"] == 1.0
    assert summary["mrr"] == 0.75
