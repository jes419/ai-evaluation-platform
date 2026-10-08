from pydantic import BaseModel


class LLMJudgeResponse(BaseModel):
    accuracy: float
    relevance: float
    completeness: float
    overall_score: float
    passed: bool
    feedback: str