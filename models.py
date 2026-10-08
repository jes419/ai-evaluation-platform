from pydantic import BaseModel, field_validator


class EvaluationRequest(BaseModel):
    prompt: str
    response: str
    reference_answer: str | None = None

    @field_validator("prompt", "response")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field must not be empty or whitespace.")
        return value

    @field_validator("reference_answer")
    @classmethod
    def validate_reference_answer(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError(
                "Reference answer must not be empty or whitespace."
            )
        return value