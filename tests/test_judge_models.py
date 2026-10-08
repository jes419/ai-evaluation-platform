import pytest
from pydantic import ValidationError

from judge_models import JudgeEvaluation


def test_valid_judge_evaluation():
    result = JudgeEvaluation(
        accuracy=90,
        relevance=95,
        completeness=85,
        overall_score=90,
        passed=True,
        feedback="The response accurately addresses the question.",
    )

    assert result.accuracy == 90
    assert result.relevance == 95
    assert result.completeness == 85
    assert result.overall_score == 90
    assert result.passed is True
    assert result.feedback == "The response accurately addresses the question."


def test_score_above_100_is_rejected():
    with pytest.raises(ValidationError):
        JudgeEvaluation(
            accuracy=101,
            relevance=95,
            completeness=85,
            overall_score=90,
            passed=True,
            feedback="Invalid score.",
        )


def test_negative_score_is_rejected():
    with pytest.raises(ValidationError):
        JudgeEvaluation(
            accuracy=-1,
            relevance=95,
            completeness=85,
            overall_score=90,
            passed=True,
            feedback="Invalid score.",
        )