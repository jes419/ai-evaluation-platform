from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

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
from llm_models import LLMJudgeResponse
from models import EvaluationRequest


app = FastAPI(
    title="AI Evaluation Platform",
    description="AI response evaluation and quality analysis API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get(
    "/evaluations",
    response_model=EvaluationHistoryResponse,
)
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


@app.get(
    "/evaluations/{evaluation_id}",
    response_model=EvaluationResponse,
)
def get_evaluation_by_id(evaluation_id: str):
    evaluation = get_evaluation(evaluation_id)

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

    scored_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.score is not None
    ]

    passed_evaluations = [
        evaluation
        for evaluation in evaluations
        if evaluation.passed is not None
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

    def average(values: list[float]) -> float:
        if not values:
            return 0.0

        return round(sum(values) / len(values), 2)

    average_score = average(
        [
            evaluation.score
            for evaluation in scored_evaluations
            if evaluation.score is not None
        ]
    )

    average_accuracy = average(
        [
            evaluation.accuracy
            for evaluation in scored_evaluations
            if evaluation.accuracy is not None
        ]
    )

    average_relevance = average(
        [
            evaluation.relevance
            for evaluation in scored_evaluations
            if evaluation.relevance is not None
        ]
    )

    average_completeness = average(
        [
            evaluation.completeness
            for evaluation in scored_evaluations
            if evaluation.completeness is not None
        ]
    )

    passed_count = sum(
        1
        for evaluation in passed_evaluations
        if evaluation.passed is True
    )

    failed_count = sum(
        1
        for evaluation in passed_evaluations
        if evaluation.passed is False
    )

    pass_rate = round(
        passed_count / len(passed_evaluations) * 100,
        2,
    ) if passed_evaluations else 0.0

    average_llm_score = average(
        [
            evaluation.llm_judge.overall_score
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        ]
    )

    average_llm_accuracy = average(
        [
            evaluation.llm_judge.accuracy
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        ]
    )

    average_llm_relevance = average(
        [
            evaluation.llm_judge.relevance
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        ]
    )

    average_llm_completeness = average(
        [
            evaluation.llm_judge.completeness
            for evaluation in llm_evaluations
            if evaluation.llm_judge is not None
        ]
    )

    average_score_difference = average(
        [
            evaluation.comparison.absolute_difference
            for evaluation in comparison_evaluations
            if evaluation.comparison is not None
        ]
    )

    return AnalyticsResponse(
        total_evaluations=total_evaluations,
        scored_evaluations=len(scored_evaluations),
        passed_evaluations=passed_count,
        failed_evaluations=failed_count,
        pass_rate=pass_rate,
        average_score=average_score,
        average_accuracy=average_accuracy,
        average_relevance=average_relevance,
        average_completeness=average_completeness,
        llm_evaluations=len(llm_evaluations),
        average_llm_score=average_llm_score,
        average_llm_accuracy=average_llm_accuracy,
        average_llm_relevance=average_llm_relevance,
        average_llm_completeness=average_llm_completeness,
        comparison_evaluations=len(comparison_evaluations),
        average_score_difference=average_score_difference,
    )