import json

from ollama import chat

from judge_models import JudgeEvaluation


class LLMJudgeUnavailableError(Exception):
    pass


class LLMJudgeResponseError(Exception):
    pass


def evaluate_with_llm(
    prompt: str,
    response: str,
    reference_answer: str,
) -> JudgeEvaluation:
    judge_prompt = f"""
Evaluate the response using the provided prompt and reference answer.

Prompt:
{prompt}

Response:
{response}

Reference Answer:
{reference_answer}

Evaluate the response using these criteria:

Accuracy: How factually correct is the response compared with the reference answer?

Relevance: How directly does the response address the prompt?

Completeness: How completely does the response cover the important information in the reference answer?

Return only these fields as valid JSON:

accuracy: number from 0 to 100
relevance: number from 0 to 100
completeness: number from 0 to 100
feedback: concise explanation of the evaluation

Do not calculate overall_score.
Do not return passed.
"""

    try:
        result = chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI response evaluator. Return only valid JSON with accuracy, relevance, completeness, and feedback.",
                },
                {
                    "role": "user",
                    "content": judge_prompt,
                },
            ],
            format={
                "type": "object",
                "properties": {
                    "accuracy": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "relevance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "completeness": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "feedback": {
                        "type": "string",
                    },
                },
                "required": [
                    "accuracy",
                    "relevance",
                    "completeness",
                    "feedback",
                ],
            },
        )
    except Exception as exc:
        raise LLMJudgeUnavailableError(
            "LLM judge is unavailable."
        ) from exc

    try:
        content = result["message"]["content"]
        data = json.loads(content)

        accuracy = float(data["accuracy"])
        relevance = float(data["relevance"])
        completeness = float(data["completeness"])
        feedback = str(data["feedback"])

        overall_score = round(
            (accuracy + relevance + completeness) / 3,
            2,
        )

        passed = overall_score >= 50

        return JudgeEvaluation(
            accuracy=accuracy,
            relevance=relevance,
            completeness=completeness,
            overall_score=overall_score,
            passed=passed,
            feedback=feedback,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LLMJudgeResponseError(
            "LLM judge returned an invalid response."
        ) from exc