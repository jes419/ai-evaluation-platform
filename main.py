from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from comparison import compare_evaluations
from evaluation_history import (
    get_evaluation,
    list_evaluations,
    save_evaluation,
)
from evaluation_models import (
    AnalyticsResponse,
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
from models import EvaluationRequest


app = FastAPI(
    title="AI Evaluation Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_validation_errors(errors):
    sanitized = []

    for error in errors:
        item = dict(error)
        ctx = item.get("ctx")

        if isinstance(ctx, dict):
            item["ctx"] = {
                key: (
                    str(value)
                    if isinstance(value, BaseException)
                    else value
                )
                for key, value in ctx.items()
            }

        sanitized.append(item)

    return sanitized


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    error_codes = {
        404: "NOT_FOUND",
        502: "LLM_JUDGE_INVALID_RESPONSE",
        503: "LLM_JUDGE_UNAVAILABLE",
    }

    code = error_codes.get(
        exc.status_code,
        "HTTP_ERROR",
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": sanitize_validation_errors(
                    exc.errors()
                ),
            }
        },
    )


@app.get("/")
def root():
    return {
        "message": "AI Evaluation Platform is running"
    }


@app.post(
    "/evaluate",
    response_model=EvaluationResponse,
)
def evaluate(request: EvaluationRequest):
    evaluation_id = str(uuid4())
    timestamp = datetime.now(timezone.utc)

    if request.reference_answer is None:
        evaluation = EvaluationResponse(
            evaluation_id=evaluation_id,
            timestamp=timestamp,
            evaluation_method="deterministic_and_llm_judge",
            score=None,
            accuracy=None,
            relevance=None,
            completeness=None,
            passed=None,
            matched_terms=[],
            missing_terms=[],
            feedback="Reference answer was not provided.",
            llm_judge=None,
            comparison=None,
        )

        return save_evaluation(evaluation)

    deterministic_result = evaluate_response(
        response=request.response,
        reference_answer=request.reference_answer,
    )

    try:
        llm_result = evaluate_with_llm(
            prompt=request.prompt,
            response=request.response,
            reference_answer=request.reference_answer,
        )
    except LLMJudgeUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except LLMJudgeResponseError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    comparison_result = compare_evaluations(
        deterministic_result=deterministic_result,
        llm_result=llm_result,
    )

    evaluation = EvaluationResponse(
        evaluation_id=evaluation_id,
        timestamp=timestamp,
        evaluation_method="deterministic_and_llm_judge",
        score=deterministic_result["score"],
        accuracy=deterministic_result["accuracy"],
        relevance=deterministic_result["relevance"],
        completeness=deterministic_result["completeness"],
        passed=deterministic_result["passed"],
        matched_terms=deterministic_result["matched_terms"],
        missing_terms=deterministic_result["missing_terms"],
        feedback=deterministic_result["feedback"],
        llm_judge=LLMJudgeResult(
            accuracy=llm_result.accuracy,
            relevance=llm_result.relevance,
            completeness=llm_result.completeness,
            overall_score=llm_result.overall_score,
            passed=llm_result.passed,
            feedback=llm_result.feedback,
        ),
        comparison=ComparisonResult(
            deterministic_score=comparison_result[
                "deterministic_score"
            ],
            llm_score=comparison_result["llm_score"],
            score_difference=comparison_result[
                "score_difference"
            ],
            absolute_difference=comparison_result[
                "absolute_difference"
            ],
            deterministic_feedback=comparison_result[
                "deterministic_feedback"
            ],
            llm_feedback=comparison_result[
                "llm_feedback"
            ],
        ),
    )

    return save_evaluation(evaluation)


@app.get(
    "/evaluations",
    response_model=EvaluationHistoryResponse,
)
def get_evaluations(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
):
    evaluations = list_evaluations()
    total = len(evaluations)

    items = evaluations[
        offset : offset + limit
    ]

    return EvaluationHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationResponse,
)
def get_evaluation_by_id(
    evaluation_id: UUID,
):
    evaluation = get_evaluation(str(evaluation_id))

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    return evaluation


@app.get(
    "/analytics",
    response_model=AnalyticsResponse,
)
def get_analytics():
    evaluations = list_evaluations()

    total_evaluations = len(evaluations)

    scored = [
        evaluation
        for evaluation in evaluations
        if evaluation.score is not None
    ]

    passed = [
        evaluation
        for evaluation in evaluations
        if evaluation.passed is True
    ]

    failed = [
        evaluation
        for evaluation in evaluations
        if evaluation.passed is False
    ]

    llm_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.llm_judge is not None
    ]

    comparison_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.comparison is not None
    ]

    scored_count = len(scored)
    passed_count = len(passed)
    failed_count = len(failed)

    pass_rate = (
        passed_count / scored_count * 100
        if scored_count
        else 0.0
    )

    average_score = (
        sum(
            evaluation.score
            for evaluation in scored
            if evaluation.score is not None
        )
        / scored_count
        if scored_count
        else 0.0
    )

    average_accuracy = (
        sum(
            evaluation.accuracy
            for evaluation in scored
            if evaluation.accuracy is not None
        )
        / scored_count
        if scored_count
        else 0.0
    )

    average_relevance = (
        sum(
            evaluation.relevance
            for evaluation in scored
            if evaluation.relevance is not None
        )
        / scored_count
        if scored_count
        else 0.0
    )

    average_completeness = (
        sum(
            evaluation.completeness
            for evaluation in scored
            if evaluation.completeness is not None
        )
        / scored_count
        if scored_count
        else 0.0
    )

    llm_count = len(llm_evaluations)

    average_llm_score = (
        sum(
            evaluation.llm_judge.overall_score
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        )
        / llm_count
        if llm_count
        else 0.0
    )

    average_llm_accuracy = (
        sum(
            evaluation.llm_judge.accuracy
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        )
        / llm_count
        if llm_count
        else 0.0
    )

    average_llm_relevance = (
        sum(
            evaluation.llm_judge.relevance
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        )
        / llm_count
        if llm_count
        else 0.0
    )

    average_llm_completeness = (
        sum(
            evaluation.llm_judge.completeness
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        )
        / llm_count
        if llm_count
        else 0.0
    )

    comparison_count = len(comparison_evaluations)

    average_score_difference = (
        sum(
            evaluation.comparison.absolute_difference
            for evaluation in comparison_evaluations
            if evaluation.comparison is not None
        )
        / comparison_count
        if comparison_count
        else 0.0
    )

    return AnalyticsResponse(
        total_evaluations=total_evaluations,
        scored_evaluations=scored_count,
        passed_evaluations=passed_count,
        failed_evaluations=failed_count,
        pass_rate=round(pass_rate, 2),
        average_score=round(average_score, 2),
        average_accuracy=round(average_accuracy, 2),
        average_relevance=round(average_relevance, 2),
        average_completeness=round(
            average_completeness,
            2,
        ),
        llm_evaluations=llm_count,
        average_llm_score=round(
            average_llm_score,
            2,
        ),
        average_llm_accuracy=round(
            average_llm_accuracy,
            2,
        ),
        average_llm_relevance=round(
            average_llm_relevance,
            2,
        ),
        average_llm_completeness=round(
            average_llm_completeness,
            2,
        ),
        comparison_evaluations=comparison_count,
        average_score_difference=round(
            average_score_difference,
            2,
        ),
    )