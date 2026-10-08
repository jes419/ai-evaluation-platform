from judge_models import JudgeEvaluation


def compare_evaluations(
    deterministic_result: dict,
    llm_result: JudgeEvaluation,
) -> dict:
    deterministic_score = float(deterministic_result["score"])
    llm_score = float(llm_result.overall_score)

    score_difference = round(
        deterministic_score - llm_score,
        2,
    )

    absolute_difference = round(
        abs(score_difference),
        2,
    )

    return {
        "deterministic_score": deterministic_score,
        "llm_score": llm_score,
        "score_difference": score_difference,
        "absolute_difference": absolute_difference,
        "deterministic_feedback": deterministic_result["feedback"],
        "llm_feedback": llm_result.feedback,
    }