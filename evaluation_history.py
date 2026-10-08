import json
from datetime import timezone

from sqlalchemy import delete, select

from database import Base, engine, SessionLocal
from evaluation_db_models import EvaluationDB
from evaluation_models import (
    ComparisonResult,
    EvaluationResponse,
    LLMJudgeResult,
)


Base.metadata.create_all(bind=engine)


def _serialize_list(values: list[str]) -> str:
    return json.dumps(values)


def _deserialize_list(value: str) -> list[str]:
    return json.loads(value)


def _to_utc_naive(timestamp):
    if timestamp is None:
        return None

    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(timezone.utc)
        timestamp = timestamp.replace(tzinfo=None)

    return timestamp


def _to_utc_aware(timestamp):
    if timestamp is None:
        return None

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(timezone.utc)


def _evaluation_to_db(evaluation: EvaluationResponse) -> EvaluationDB:
    if evaluation.evaluation_id is None:
        raise ValueError("Evaluation ID is required.")

    llm_judge = evaluation.llm_judge
    comparison = evaluation.comparison

    return EvaluationDB(
        evaluation_id=evaluation.evaluation_id,
        timestamp=_to_utc_naive(evaluation.timestamp),
        evaluation_method=evaluation.evaluation_method
        or "deterministic_and_llm_judge",
        score=evaluation.score,
        accuracy=evaluation.accuracy,
        relevance=evaluation.relevance,
        completeness=evaluation.completeness,
        passed=evaluation.passed,
        matched_terms=_serialize_list(evaluation.matched_terms),
        missing_terms=_serialize_list(evaluation.missing_terms),
        feedback=evaluation.feedback,
        llm_accuracy=llm_judge.accuracy if llm_judge else None,
        llm_relevance=llm_judge.relevance if llm_judge else None,
        llm_completeness=llm_judge.completeness if llm_judge else None,
        llm_overall_score=llm_judge.overall_score if llm_judge else None,
        llm_passed=llm_judge.passed if llm_judge else None,
        llm_feedback=llm_judge.feedback if llm_judge else None,
        deterministic_score=(
            comparison.deterministic_score
            if comparison
            else None
        ),
        comparison_llm_score=(
            comparison.llm_score
            if comparison
            else None
        ),
        score_difference=(
            comparison.score_difference
            if comparison
            else None
        ),
        absolute_difference=(
            comparison.absolute_difference
            if comparison
            else None
        ),
        deterministic_feedback=(
            comparison.deterministic_feedback
            if comparison
            else None
        ),
        comparison_llm_feedback=(
            comparison.llm_feedback
            if comparison
            else None
        ),
    )


def _db_to_evaluation(row: EvaluationDB) -> EvaluationResponse:
    llm_judge = None

    if row.llm_accuracy is not None:
        llm_judge = LLMJudgeResult(
            accuracy=row.llm_accuracy,
            relevance=row.llm_relevance or 0,
            completeness=row.llm_completeness or 0,
            overall_score=row.llm_overall_score or 0,
            passed=row.llm_passed or False,
            feedback=row.llm_feedback or "",
        )

    comparison = None

    if row.deterministic_score is not None:
        comparison = ComparisonResult(
            deterministic_score=row.deterministic_score,
            llm_score=row.comparison_llm_score or 0,
            score_difference=row.score_difference or 0,
            absolute_difference=row.absolute_difference or 0,
            deterministic_feedback=row.deterministic_feedback or "",
            llm_feedback=row.comparison_llm_feedback or "",
        )

    return EvaluationResponse(
        evaluation_id=row.evaluation_id,
        timestamp=_to_utc_aware(row.timestamp),
        evaluation_method=row.evaluation_method,
        score=row.score,
        accuracy=row.accuracy,
        relevance=row.relevance,
        completeness=row.completeness,
        passed=row.passed,
        matched_terms=_deserialize_list(row.matched_terms),
        missing_terms=_deserialize_list(row.missing_terms),
        feedback=row.feedback,
        llm_judge=llm_judge,
        comparison=comparison,
    )


def save_evaluation(evaluation: EvaluationResponse) -> EvaluationResponse:
    if evaluation.evaluation_id is None:
        raise ValueError("Evaluation ID is required.")

    with SessionLocal() as db:
        existing = db.scalar(
            select(EvaluationDB).where(
                EvaluationDB.evaluation_id
                == evaluation.evaluation_id
            )
        )

        if existing is not None:
            existing.timestamp = _to_utc_naive(
                evaluation.timestamp
            )
            existing.evaluation_method = (
                evaluation.evaluation_method
                or "deterministic_and_llm_judge"
            )
            existing.score = evaluation.score
            existing.accuracy = evaluation.accuracy
            existing.relevance = evaluation.relevance
            existing.completeness = evaluation.completeness
            existing.passed = evaluation.passed
            existing.matched_terms = _serialize_list(
                evaluation.matched_terms
            )
            existing.missing_terms = _serialize_list(
                evaluation.missing_terms
            )
            existing.feedback = evaluation.feedback

            db.commit()

            return evaluation

        row = _evaluation_to_db(evaluation)

        db.add(row)
        db.commit()

        return evaluation


def get_evaluation(
    evaluation_id: str,
) -> EvaluationResponse | None:
    with SessionLocal() as db:
        row = db.scalar(
            select(EvaluationDB).where(
                EvaluationDB.evaluation_id == evaluation_id
            )
        )

        if row is None:
            return None

        return _db_to_evaluation(row)


def list_evaluations() -> list[EvaluationResponse]:
    with SessionLocal() as db:
        rows = db.scalars(
            select(EvaluationDB).order_by(EvaluationDB.id)
        ).all()

        return [
            _db_to_evaluation(row)
            for row in rows
        ]


def clear_evaluations() -> None:
    with SessionLocal() as db:
        db.execute(delete(EvaluationDB))
        db.commit()