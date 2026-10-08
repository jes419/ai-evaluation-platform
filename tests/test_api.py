from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from evaluation_history import clear_evaluations
from judge import LLMJudgeResponseError, LLMJudgeUnavailableError
from main import app


client = TestClient(app)


def setup_function():
    clear_evaluations()


def teardown_function():
    clear_evaluations()


def create_evaluation(prompt: str, response: str):
    return client.post(
        "/evaluate",
        json={
            "prompt": prompt,
            "response": response,
        },
    )


def assert_validation_error(response):
    assert response.status_code == 422

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    assert isinstance(data["error"]["details"], list)

    return data["error"]["details"]


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "AI Evaluation Platform is running"
    }


def test_analytics_returns_empty_metrics_initially():
    response = client.get("/analytics")

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "total_evaluations": 0,
        "scored_evaluations": 0,
        "passed_evaluations": 0,
        "failed_evaluations": 0,
        "pass_rate": 0.0,
        "average_score": 0.0,
        "average_accuracy": 0.0,
        "average_relevance": 0.0,
        "average_completeness": 0.0,
        "llm_evaluations": 0,
        "average_llm_score": 0.0,
        "average_llm_accuracy": 0.0,
        "average_llm_relevance": 0.0,
        "average_llm_completeness": 0.0,
        "comparison_evaluations": 0,
        "average_score_difference": 0.0,
    }


def test_evaluate_without_reference_answer():
    response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["score"] is None
    assert data["accuracy"] is None
    assert data["relevance"] is None
    assert data["completeness"] is None
    assert data["passed"] is None
    assert data["llm_judge"] is None
    assert data["comparison"] is None
    assert data["evaluation_method"] == "deterministic_and_llm_judge"

    UUID(data["evaluation_id"])

    timestamp = datetime.fromisoformat(
        data["timestamp"].replace("Z", "+00:00")
    )

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_evaluate_metadata_contains_valid_evaluation_id():
    response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    assert response.status_code == 200

    data = response.json()

    evaluation_id = UUID(data["evaluation_id"])

    assert str(evaluation_id) == data["evaluation_id"]


def test_evaluate_metadata_contains_valid_utc_timestamp():
    response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    assert response.status_code == 200

    data = response.json()

    timestamp = datetime.fromisoformat(
        data["timestamp"].replace("Z", "+00:00")
    )

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_evaluate_metadata_contains_correct_evaluation_method():
    response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evaluation_method"] == "deterministic_and_llm_judge"


def test_evaluate_generates_unique_evaluation_ids():
    first_response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    second_response = create_evaluation(
        "What is JavaScript?",
        "JavaScript is a programming language.",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_id = first_response.json()["evaluation_id"]
    second_id = second_response.json()["evaluation_id"]

    assert first_id != second_id


def test_get_evaluations_returns_empty_list_initially():
    response = client.get("/evaluations")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_evaluations_returns_saved_evaluations():
    first_response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    second_response = create_evaluation(
        "What is JavaScript?",
        "JavaScript is a programming language.",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_data = first_response.json()
    second_data = second_response.json()

    response = client.get("/evaluations")

    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    assert len(items) == 2
    assert data["total"] == 2
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert items[0]["evaluation_id"] == first_data["evaluation_id"]
    assert items[1]["evaluation_id"] == second_data["evaluation_id"]


def test_get_evaluations_respects_limit():
    create_evaluation("Question 1", "Response 1")
    create_evaluation("Question 2", "Response 2")
    create_evaluation("Question 3", "Response 3")

    response = client.get("/evaluations?limit=2")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_get_evaluations_respects_offset():
    first_response = create_evaluation(
        "Question 1",
        "Response 1",
    )

    second_response = create_evaluation(
        "Question 2",
        "Response 2",
    )

    create_evaluation(
        "Question 3",
        "Response 3",
    )

    response = client.get("/evaluations?offset=1")

    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    assert len(items) == 2
    assert data["total"] == 3
    assert data["limit"] == 10
    assert data["offset"] == 1
    assert items[0]["evaluation_id"] == second_response.json()["evaluation_id"]
    assert items[0]["evaluation_id"] != first_response.json()["evaluation_id"]


def test_get_evaluations_respects_limit_and_offset():
    create_evaluation("Question 1", "Response 1")

    second_response = create_evaluation(
        "Question 2",
        "Response 2",
    )

    third_response = create_evaluation(
        "Question 3",
        "Response 3",
    )

    create_evaluation("Question 4", "Response 4")

    response = client.get("/evaluations?limit=2&offset=1")

    assert response.status_code == 200

    data = response.json()
    items = data["items"]

    assert len(items) == 2
    assert data["total"] == 4
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert items[0]["evaluation_id"] == second_response.json()["evaluation_id"]
    assert items[1]["evaluation_id"] == third_response.json()["evaluation_id"]


def test_get_evaluations_accepts_minimum_limit():
    response = client.get("/evaluations?limit=1")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 1
    assert data["offset"] == 0


def test_get_evaluations_accepts_maximum_limit():
    response = client.get("/evaluations?limit=100")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 100
    assert data["offset"] == 0


def test_get_evaluations_accepts_zero_offset():
    response = client.get("/evaluations?offset=0")

    assert response.status_code == 200

    data = response.json()

    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_evaluations_rejects_zero_limit():
    response = client.get("/evaluations?limit=0")

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "limit"
        for detail in details
    )


def test_get_evaluations_rejects_limit_above_maximum():
    response = client.get("/evaluations?limit=101")

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "limit"
        for detail in details
    )


def test_get_evaluations_rejects_negative_offset():
    response = client.get("/evaluations?offset=-1")

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "offset"
        for detail in details
    )


def test_get_evaluations_rejects_non_integer_limit():
    response = client.get("/evaluations?limit=abc")

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "limit"
        for detail in details
    )


def test_get_evaluations_rejects_non_integer_offset():
    response = client.get("/evaluations?offset=abc")

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "offset"
        for detail in details
    )


def test_get_evaluation_by_id_returns_saved_evaluation():
    create_response = create_evaluation(
        "What is Python?",
        "Python is a programming language.",
    )

    assert create_response.status_code == 200

    created_data = create_response.json()
    evaluation_id = created_data["evaluation_id"]

    response = client.get(f"/evaluations/{evaluation_id}")

    assert response.status_code == 200
    assert response.json() == created_data


def test_get_evaluation_by_id_returns_404_for_unknown_id():
    response = client.get(
        "/evaluations/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Evaluation not found.",
        }
    }


def test_get_evaluation_by_id_rejects_invalid_uuid():
    response = client.get(
        "/evaluations/not-a-valid-uuid"
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "evaluation_id"
        for detail in details
    )


def test_evaluate_requires_prompt():
    response = client.post(
        "/evaluate",
        json={
            "response": "Python is a programming language.",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "prompt"
        for detail in details
    )


def test_evaluate_requires_response():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "response"
        for detail in details
    )


def test_evaluate_rejects_empty_prompt():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "",
            "response": "Python is a programming language.",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "prompt"
        for detail in details
    )


def test_evaluate_rejects_empty_response():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "response"
        for detail in details
    )


def test_evaluate_rejects_whitespace_prompt():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "   ",
            "response": "Python is a programming language.",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "prompt"
        for detail in details
    )


def test_evaluate_rejects_whitespace_response():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "   ",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "response"
        for detail in details
    )


def test_evaluate_rejects_empty_reference_answer():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": "",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "reference_answer"
        for detail in details
    )


def test_evaluate_rejects_whitespace_reference_answer():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": "   ",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "reference_answer"
        for detail in details
    )


def test_evaluate_rejects_invalid_json_shape():
    response = client.post(
        "/evaluate",
        json={
            "prompt": 123,
            "response": "Python is a programming language.",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "prompt"
        for detail in details
    )


def test_evaluate_rejects_invalid_response_type():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": 123,
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "response"
        for detail in details
    )


def test_evaluate_rejects_invalid_reference_answer_type():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": 123,
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "reference_answer"
        for detail in details
    )


def test_evaluate_rejects_null_prompt():
    response = client.post(
        "/evaluate",
        json={
            "prompt": None,
            "response": "Python is a programming language.",
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "prompt"
        for detail in details
    )


def test_evaluate_rejects_null_response():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": None,
            "reference_answer": "Python is a programming language.",
        },
    )

    details = assert_validation_error(response)

    assert any(
        detail["loc"][-1] == "response"
        for detail in details
    )


def test_evaluate_accepts_null_reference_answer():
    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reference_answer"] if "reference_answer" in data else True
    assert data["score"] is None
    assert data["llm_judge"] is None
    assert data["comparison"] is None


def test_evaluate_returns_503_when_llm_unavailable(monkeypatch):
    def mock_evaluate_with_llm(*args, **kwargs):
        raise LLMJudgeUnavailableError(
            "LLM judge is unavailable."
        )

    monkeypatch.setattr(
        "main.evaluate_with_llm",
        mock_evaluate_with_llm,
    )

    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": "Python is a high-level programming language.",
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "error": {
            "code": "LLM_JUDGE_UNAVAILABLE",
            "message": "LLM judge is unavailable.",
        }
    }


def test_evaluate_returns_502_when_llm_response_is_invalid(monkeypatch):
    def mock_evaluate_with_llm(*args, **kwargs):
        raise LLMJudgeResponseError(
            "LLM judge returned an invalid response."
        )

    monkeypatch.setattr(
        "main.evaluate_with_llm",
        mock_evaluate_with_llm,
    )

    response = client.post(
        "/evaluate",
        json={
            "prompt": "What is Python?",
            "response": "Python is a programming language.",
            "reference_answer": "Python is a high-level programming language.",
        },
    )

    assert response.status_code == 502

    assert response.json() == {
        "error": {
            "code": "LLM_JUDGE_INVALID_RESPONSE",
            "message": "LLM judge returned an invalid response.",
        }
    }