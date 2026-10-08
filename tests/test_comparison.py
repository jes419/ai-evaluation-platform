from comparison import compare_evaluations
from judge_models import JudgeEvaluation


def test_compare_evaluations():
    deterministic_result = {
        "score": 83.33,
        "feedback": "Response has strong alignment with the reference answer.",
    }

    llm_result = JudgeEvaluation(
        accuracy=70,
        relevance=100,
        completeness=50,
        overall_score=73.3,
        passed=True,
        feedback="The response is relevant but incomplete.",
    )

    result = compare_evaluations(
        deterministic_result,
        llm_result,
    )

    assert result["deterministic_score"] == 83.33
    assert result["llm_score"] == 73.3
    assert result["score_difference"] == 10.03
    assert result["absolute_difference"] == 10.03
    assert result["deterministic_feedback"] == deterministic_result["feedback"]
    assert result["llm_feedback"] == llm_result.feedback