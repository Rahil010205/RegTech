"""Retrieval evaluation using real BGE embeddings and labeled queries."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.retrieval.retriever import Retriever
from app.retrieval.schemas import RetrievalFilters
from tests.evaluation.retrieval_metrics import (
    RetrievalEvalCase,
    evaluate_case,
    summarize_results,
)


EVAL_CASES = [
    RetrievalEvalCase(
        query="What are the requirements for customer data retention?",
        expected_text_snippets=("seven years", "retain customer records"),
    ),
    RetrievalEvalCase(
        query="How long must customer records be kept?",
        expected_text_snippets=("seven years",),
    ),
    RetrievalEvalCase(
        query="What security controls are required for protecting customer information?",
        expected_text_snippets=("security controls", "encryption"),
    ),
    RetrievalEvalCase(
        query="What encryption requirements apply?",
        expected_text_snippets=("aes-256", "encryption"),
    ),
    RetrievalEvalCase(
        query="What is the capital of France?",
        expected_text_snippets=("paris",),
    ),
]


@pytest.mark.integration
@pytest.mark.evaluation
@pytest.mark.slow
def test_retrieval_evaluation_metrics(
    db_session: Session,
    real_embedded_document: dict[str, Any],
) -> None:
    retriever = Retriever(db_session)
    filters = RetrievalFilters(document_id=real_embedded_document["version_id"])
    eval_results = []

    for case in EVAL_CASES:
        response = retriever.retrieve(case.query, top_k=5, filters=filters)
        texts = [result.text for result in response.results]
        eval_results.append(evaluate_case(case, texts))

    metrics = summarize_results(eval_results[:-1])
    unrelated = eval_results[-1]

    assert metrics["hit_at_1"] >= 0.75
    assert metrics["hit_at_3"] == 1.0
    assert metrics["hit_at_5"] == 1.0
    assert metrics["mrr"] >= 0.85
    assert unrelated.reciprocal_rank == 0.0

    print(
        {
            "hit_at_1": round(metrics["hit_at_1"], 3),
            "hit_at_3": round(metrics["hit_at_3"], 3),
            "hit_at_5": round(metrics["hit_at_5"], 3),
            "mrr": round(metrics["mrr"], 3),
            "unrelated_top_similarity_query": unrelated.query,
            "unrelated_top_text": unrelated.top_text[:120],
        }
    )
