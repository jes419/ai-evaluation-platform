from datetime import datetime

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    score: float | None
    accuracy: float | None
    relevance: float | None
    completeness: float | None
    passed: bool | None
    matched_terms: list[str]
    missing_terms: list[str]
    feedback: str


class LLMJudgeResult(BaseModel):
    accuracy: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    passed: bool
    feedback: str


class ComparisonResult(BaseModel):
    deterministic_score: float = Field(ge=0, le=100)
    llm_score: float = Field(ge=0, le=100)
    score_difference: float
    absolute_difference: float = Field(ge=0)
    deterministic_feedback: str
    llm_feedback: str


class EvaluationMetadata(BaseModel):
    evaluation_id: str
    timestamp: datetime
    evaluation_method: str


class EvaluationResponse(BaseModel):
    evaluation_id: str | None = None
    timestamp: datetime | None = None
    evaluation_method: str | None = None
    score: float | None
    accuracy: float | None
    relevance: float | None
    completeness: float | None
    passed: bool | None
    matched_terms: list[str]
    missing_terms: list[str]
    feedback: str
    llm_judge: LLMJudgeResult | None
    comparison: ComparisonResult | None


class EvaluationHistoryResponse(BaseModel):
    items: list[EvaluationResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)