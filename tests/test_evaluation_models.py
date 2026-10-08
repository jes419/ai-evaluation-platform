import pytest
from pydantic import ValidationError

from evaluation_models import (
    ComparisonResult,
    EvaluationResponse,
    EvaluationResult,
    LLMJudgeResult,
)


def test_valid_evaluation_result():
    result = EvaluationResult(
        score=85,
        accuracy=90,
        relevance=80,
        completeness=85,
        passed=True,
        matched_terms=["python", "programming"],
        missing_terms=["high-level"],
        feedback="Strong response.",
    )

    assert result.score == 85
    assert result.accuracy == 90
    assert result.relevance == 80
    assert result.completeness == 85
    assert result.passed is True
    assert result.matched_terms == ["python", "programming"]
    assert result.missing_terms == ["high-level"]
    assert result.feedback == "Strong response."


def test_valid_llm_judge_result():
    result = LLMJudgeResult(
        accuracy=90,
        relevance=95,
        completeness=85,
        overall_score=90,
        passed=True,
        feedback="The response is accurate and relevant.",
    )

    assert result.accuracy == 90
    assert result.relevance == 95
    assert result.completeness == 85
    assert result.overall_score == 90
    assert result.passed is True
    assert result.feedback == "The response is accurate and relevant."


def test_llm_judge_result_rejects_score_above_100():
    with pytest.raises(ValidationError):
        LLMJudgeResult(
            accuracy=101,
            relevance=95,
            completeness=85,
            overall_score=90,
            passed=True,
            feedback="Invalid score.",
        )


def test_llm_judge_result_rejects_negative_score():
    with pytest.raises(ValidationError):
        LLMJudgeResult(
            accuracy=-1,
            relevance=95,
            completeness=85,
            overall_score=90,
            passed=True,
            feedback="Invalid score.",
        )


def test_llm_judge_result_rejects_negative_overall_score():
    with pytest.raises(ValidationError):
        LLMJudgeResult(
            accuracy=90,
            relevance=95,
            completeness=85,
            overall_score=-1,
            passed=True,
            feedback="Invalid score.",
        )


def test_valid_comparison_result():
    result = ComparisonResult(
        deterministic_score=83.33,
        llm_score=86.67,
        score_difference=-3.34,
        absolute_difference=3.34,
        deterministic_feedback="Strong alignment.",
        llm_feedback="Accurate and relevant.",
    )

    assert result.deterministic_score == 83.33
    assert result.llm_score == 86.67
    assert result.score_difference == -3.34
    assert result.absolute_difference == 3.34
    assert result.deterministic_feedback == "Strong alignment."
    assert result.llm_feedback == "Accurate and relevant."


def test_comparison_result_rejects_deterministic_score_above_100():
    with pytest.raises(ValidationError):
        ComparisonResult(
            deterministic_score=101,
            llm_score=86.67,
            score_difference=14.33,
            absolute_difference=14.33,
            deterministic_feedback="Invalid.",
            llm_feedback="Valid.",
        )


def test_comparison_result_rejects_llm_score_above_100():
    with pytest.raises(ValidationError):
        ComparisonResult(
            deterministic_score=83.33,
            llm_score=101,
            score_difference=-17.67,
            absolute_difference=17.67,
            deterministic_feedback="Valid.",
            llm_feedback="Invalid.",
        )


def test_comparison_result_rejects_negative_absolute_difference():
    with pytest.raises(ValidationError):
        ComparisonResult(
            deterministic_score=83.33,
            llm_score=86.67,
            score_difference=-3.34,
            absolute_difference=-3.34,
            deterministic_feedback="Valid.",
            llm_feedback="Valid.",
        )


def test_valid_evaluation_response_without_llm_judge():
    result = EvaluationResponse(
        score=None,
        accuracy=None,
        relevance=None,
        completeness=None,
        passed=None,
        matched_terms=[],
        missing_terms=[],
        feedback="No reference answer was provided.",
        llm_judge=None,
        comparison=None,
    )

    assert result.score is None
    assert result.llm_judge is None
    assert result.comparison is None


def test_valid_evaluation_response_with_nested_models():
    llm_judge = LLMJudgeResult(
        accuracy=90,
        relevance=95,
        completeness=85,
        overall_score=90,
        passed=True,
        feedback="Strong evaluation.",
    )

    comparison = ComparisonResult(
        deterministic_score=83.33,
        llm_score=90,
        score_difference=-6.67,
        absolute_difference=6.67,
        deterministic_feedback="Good alignment.",
        llm_feedback="Strong response.",
    )

    result = EvaluationResponse(
        score=83.33,
        accuracy=75,
        relevance=100,
        completeness=75,
        passed=True,
        matched_terms=["python"],
        missing_terms=["high-level"],
        feedback="Strong alignment.",
        llm_judge=llm_judge,
        comparison=comparison,
    )

    assert result.score == 83.33
    assert result.llm_judge.accuracy == 90
    assert result.llm_judge.overall_score == 90
    assert result.comparison.deterministic_score == 83.33
    assert result.comparison.llm_score == 90