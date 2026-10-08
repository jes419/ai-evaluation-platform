from datetime import datetime, timezone

import pytest

from evaluation_history import (
    clear_evaluations,
    get_evaluation,
    list_evaluations,
    save_evaluation,
)
from evaluation_models import EvaluationResponse


@pytest.fixture(autouse=True)
def reset_history():
    clear_evaluations()
    yield
    clear_evaluations()


def create_evaluation(
    evaluation_id: str = "test-evaluation-1",
) -> EvaluationResponse:
    return EvaluationResponse(
        evaluation_id=evaluation_id,
        timestamp=datetime.now(timezone.utc),
        evaluation_method="deterministic_and_llm_judge",
        score=90,
        accuracy=90,
        relevance=90,
        completeness=90,
        passed=True,
        matched_terms=["python"],
        missing_terms=[],
        feedback="Strong alignment.",
        llm_judge=None,
        comparison=None,
    )


def test_save_evaluation():
    evaluation = create_evaluation()

    result = save_evaluation(evaluation)

    assert result == evaluation
    assert get_evaluation("test-evaluation-1") == evaluation


def test_get_evaluation_returns_saved_evaluation():
    evaluation = create_evaluation()

    save_evaluation(evaluation)

    result = get_evaluation("test-evaluation-1")

    assert result == evaluation


def test_get_evaluation_returns_none_for_unknown_id():
    result = get_evaluation("unknown-evaluation")

    assert result is None


def test_list_evaluations_returns_saved_evaluations():
    first = create_evaluation("evaluation-1")
    second = create_evaluation("evaluation-2")

    save_evaluation(first)
    save_evaluation(second)

    result = list_evaluations()

    assert result == [first, second]


def test_list_evaluations_returns_empty_list_when_no_evaluations_exist():
    result = list_evaluations()

    assert result == []


def test_save_evaluation_updates_existing_evaluation():
    original = create_evaluation("evaluation-1")
    updated = EvaluationResponse(
        evaluation_id="evaluation-1",
        timestamp=datetime.now(timezone.utc),
        evaluation_method="deterministic_and_llm_judge",
        score=95,
        accuracy=95,
        relevance=95,
        completeness=95,
        passed=True,
        matched_terms=["python", "programming"],
        missing_terms=[],
        feedback="Updated evaluation.",
        llm_judge=None,
        comparison=None,
    )

    save_evaluation(original)
    save_evaluation(updated)

    result = get_evaluation("evaluation-1")

    assert result == updated
    assert len(list_evaluations()) == 1


def test_save_evaluation_requires_evaluation_id():
    evaluation = EvaluationResponse(
        evaluation_id=None,
        timestamp=datetime.now(timezone.utc),
        evaluation_method="deterministic_and_llm_judge",
        score=90,
        accuracy=90,
        relevance=90,
        completeness=90,
        passed=True,
        matched_terms=["python"],
        missing_terms=[],
        feedback="Strong alignment.",
        llm_judge=None,
        comparison=None,
    )

    with pytest.raises(ValueError, match="Evaluation ID is required."):
        save_evaluation(evaluation)


def test_clear_evaluations_removes_all_evaluations():
    first = create_evaluation("evaluation-1")
    second = create_evaluation("evaluation-2")

    save_evaluation(first)
    save_evaluation(second)

    clear_evaluations()

    assert list_evaluations() == []
    assert get_evaluation("evaluation-1") is None
    assert get_evaluation("evaluation-2") is None