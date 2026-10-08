from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query

from comparison import compare_evaluations
from evaluation_history import (
    get_evaluation,
    list_evaluations,
    save_evaluation,
)
from evaluation_models import (
    ComparisonResult,
    EvaluationHistoryResponse,
    EvaluationResponse,
    LLMJudgeResult,
)
from evaluator import evaluate_response
from judge import (
    LLMJudgeResponseError,
    LLMJudgeUnavailableError,
    evaluate_with_llm,
)
from llm_models import LLMJudgeResponse
from models import EvaluationRequest


app = FastAPI()


@app.get("/")
def root():
    return {"message": "AI Evaluation Platform is running"}


@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest):
    evaluation_id = str(uuid4())
    timestamp = datetime.now(timezone.utc)
    evaluation_method = "deterministic_and_llm_judge"

    if request.reference_answer is None:
        evaluation = EvaluationResponse(
            evaluation_id=evaluation_id,
            timestamp=timestamp,
            evaluation_method=evaluation_method,
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

        return save_evaluation(evaluation)

    deterministic_result = evaluate_response(
        request.response,
        request.reference_answer,
    )

    try:
        llm_result = evaluate_with_llm(
            request.prompt,
            request.response,
            request.reference_answer,
        )
    except LLMJudgeUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="LLM judge is unavailable.",
        ) from exc
    except LLMJudgeResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail="LLM judge returned an invalid response.",
        ) from exc

    llm_judge = LLMJudgeResult(
        accuracy=llm_result.accuracy,
        relevance=llm_result.relevance,
        completeness=llm_result.completeness,
        overall_score=llm_result.overall_score,
        passed=llm_result.passed,
        feedback=llm_result.feedback,
    )

    llm_judge_for_comparison = LLMJudgeResponse(
        accuracy=llm_judge.accuracy,
        relevance=llm_judge.relevance,
        completeness=llm_judge.completeness,
        overall_score=llm_judge.overall_score,
        passed=llm_judge.passed,
        feedback=llm_judge.feedback,
    )

    comparison_result = compare_evaluations(
        deterministic_result,
        llm_judge_for_comparison,
    )

    comparison = ComparisonResult(
        **comparison_result,
    )

    evaluation = EvaluationResponse(
        evaluation_id=evaluation_id,
        timestamp=timestamp,
        evaluation_method=evaluation_method,
        **deterministic_result,
        llm_judge=llm_judge,
        comparison=comparison,
    )

    return save_evaluation(evaluation)


@app.get("/evaluations", response_model=EvaluationHistoryResponse)
def get_evaluations(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    evaluations = list_evaluations()
    total = len(evaluations)
    items = evaluations[offset : offset + limit]

    return EvaluationHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation_by_id(evaluation_id: str):
    evaluation = get_evaluation(evaluation_id)

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    return evaluation