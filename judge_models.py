from pydantic import BaseModel, Field


class JudgeEvaluation(BaseModel):
    accuracy: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    passed: bool
    feedback: str