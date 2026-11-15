from unittest.mock import Mock

import pytest

from judge import (
    LLMJudgeResponseError,
    LLMJudgeUnavailableError,
    evaluate_with_llm,
)
from judge_models import JudgeEvaluation


def test_llm_judge_returns_valid_evaluation(monkeypatch):
    mock_chat = Mock(
        return_value={
            "message": {
                "content": (
                    '{"accuracy": 90, "relevance": 75, '
                    '"completeness": 60, '
                    '"feedback": "Covers the main points."}'
                )
            }
        }
    )
    monkeypatch.setattr("judge.chat", mock_chat)

    result = evaluate_with_llm(
        prompt="What is Python?",
        response="Python is a programming language.",
        reference_answer="Python is a high-level programming language.",
    )

    assert isinstance(result, JudgeEvaluation)
    assert result.accuracy == 90
    assert result.relevance == 75
    assert result.completeness == 60
    assert result.overall_score == 75
    assert result.passed is True
    assert result.feedback == "Covers the main points."

    mock_chat.assert_called_once()
    call_kwargs = mock_chat.call_args.kwargs
    assert call_kwargs["model"] == "qwen3:8b"
    assert call_kwargs["messages"][0]["role"] == "system"
    assert call_kwargs["messages"][1]["role"] == "user"
    assert call_kwargs["format"]["type"] == "object"
    assert set(call_kwargs["format"]["required"]) == {
        "accuracy",
        "relevance",
        "completeness",
        "feedback",
    }
    assert "What is Python?" in call_kwargs["messages"][1]["content"]
    assert (
        "Python is a programming language."
        in call_kwargs["messages"][1]["content"]
    )
    assert (
        "Python is a high-level programming language."
        in call_kwargs["messages"][1]["content"]
    )


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
