import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "was",
    "were",
    "with",
}


ACCURACY_WEIGHT = 0.4
RELEVANCE_WEIGHT = 0.3
COMPLETENESS_WEIGHT = 0.3


def normalize_text(text: str) -> set[str]:
    text = text.lower()
    words = re.findall(r"[\w]+(?:-[\w]+)*", text)
    return set(words) - STOP_WORDS


def calculate_accuracy(
    response_words: set[str],
    reference_words: set[str],
) -> float:
    if not reference_words:
        return 0.0

    matched_words = response_words & reference_words

    return round(
        len(matched_words) / len(reference_words) * 100,
        2,
    )


def calculate_relevance(
    response_words: set[str],
    reference_words: set[str],
) -> float:
    if not response_words:
        return 0.0

    matched_words = response_words & reference_words

    return round(
        len(matched_words) / len(response_words) * 100,
        2,
    )


def calculate_completeness(
    response_words: set[str],
    reference_words: set[str],
) -> float:
    if not reference_words:
        return 0.0

    matched_words = response_words & reference_words

    return round(
        len(matched_words) / len(reference_words) * 100,
        2,
    )


def calculate_overall_score(
    accuracy: float,
    relevance: float,
    completeness: float,
) -> float:
    return round(
        (
            accuracy * ACCURACY_WEIGHT
            + relevance * RELEVANCE_WEIGHT
            + completeness * COMPLETENESS_WEIGHT
        ),
        2,
    )


def evaluate_response(
    response: str,
    reference_answer: str,
) -> dict:
    response_words = normalize_text(response)
    reference_words = normalize_text(reference_answer)

    if not reference_words:
        return {
            "score": 0,
            "accuracy": 0,
            "relevance": 0,
            "completeness": 0,
            "passed": False,
            "matched_terms": [],
            "missing_terms": [],
            "feedback": "Reference answer is empty.",
        }

    overlap = response_words & reference_words
    missing = reference_words - response_words

    accuracy = calculate_accuracy(
        response_words,
        reference_words,
    )

    relevance = calculate_relevance(
        response_words,
        reference_words,
    )

    completeness = calculate_completeness(
        response_words,
        reference_words,
    )

    score = calculate_overall_score(
        accuracy,
        relevance,
        completeness,
    )

    if score >= 80:
        feedback = "Response has strong alignment with the reference answer."
    elif score >= 50:
        feedback = "Response has moderate alignment with the reference answer."
    else:
        feedback = "Response has weak alignment with the reference answer."

    return {
        "score": score,
        "accuracy": accuracy,
        "relevance": relevance,
        "completeness": completeness,
        "passed": score >= 50,
        "matched_terms": sorted(overlap),
        "missing_terms": sorted(missing),
        "feedback": feedback,
    }