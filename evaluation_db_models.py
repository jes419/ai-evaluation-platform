from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class EvaluationDB(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    evaluation_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    evaluation_method: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    relevance: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    completeness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    matched_terms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    missing_terms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    feedback: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    llm_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    llm_relevance: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    llm_completeness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    llm_overall_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    llm_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    llm_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    deterministic_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    comparison_llm_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    score_difference: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    absolute_difference: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    deterministic_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    comparison_llm_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )