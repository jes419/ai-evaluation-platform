import pytest

from judge import (
    LLMJudgeResponseError,
    LLMJudgeUnavailableError,
    evaluate_with_llm,
)
from judge_models import JudgeEvaluation


def test_llm_judge_returns_valid_evaluation():
    result = evaluate_with_llm(
        prompt="What is Python?",
        response="Python is a programming language.",
        reference_answer="Python is a high-level programming language.",
    )

    assert isinstance(result, JudgeEvaluation)
    assert 0 <= result.accuracy <= 100
    assert 0 <= result.relevance <= 100
    assert 0 <= result.completeness <= 100
    assert 0 <= result.overall_score <= 100
    assert isinstance(result.passed, bool)
    assert isinstance(result.feedback, str)
    assert result.feedback


def test_llm_judge_unavailable(monkeypatch):
    def mock_chat(*args, **kwargs):
        raise RuntimeError("Ollama is unavailable")

    monkeypatch.setattr("judge.chat", mock_chat)

    with pytest.raises(LLMJudgeUnavailableError, match="LLM judge is unavailable."):
        evaluate_with_llm(
            prompt="What is Python?",
            response="Python is a programming language.",
            reference_answer="Python is a high-level programming language.",
        )


def test_llm_judge_invalid_response(monkeypatch):
    def mock_chat(*args, **kwargs):
        return {
            "message": {
                "content": "invalid json"
            }
        }

    monkeypatch.setattr("judge.chat", mock_chat)

    with pytest.raises(
        LLMJudgeResponseError,
        match="LLM judge returned an invalid response.",
    ):
        evaluate_with_llm(
            prompt="What is Python?",
            response="Python is a programming language.",
            reference_answer="Python is a high-level programming language.",
        )


def test_llm_judge_missing_field(monkeypatch):
    def mock_chat(*args, **kwargs):
        return {
            "message": {
                "content": """
                {
                    "accuracy": 90,
                    "relevance": 95,
                    "feedback": "Good response."
                }
                """
            }
        }

    monkeypatch.setattr("judge.chat", mock_chat)

    with pytest.raises(
        LLMJudgeResponseError,
        match="LLM judge returned an invalid response.",
    ):
        evaluate_with_llm(
            prompt="What is Python?",
            response="Python is a programming language.",
            reference_answer="Python is a high-level programming language.",
        )