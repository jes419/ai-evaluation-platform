from evaluation_models import EvaluationResponse


_evaluation_history: dict[str, EvaluationResponse] = {}


def save_evaluation(evaluation: EvaluationResponse) -> EvaluationResponse:
    if evaluation.evaluation_id is None:
        raise ValueError("Evaluation ID is required.")

    _evaluation_history[evaluation.evaluation_id] = evaluation

    return evaluation


def get_evaluation(evaluation_id: str) -> EvaluationResponse | None:
    return _evaluation_history.get(evaluation_id)


def list_evaluations() -> list[EvaluationResponse]:
    return list(_evaluation_history.values())


def clear_evaluations() -> None:
    _evaluation_history.clear()