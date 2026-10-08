from evaluator import (
    calculate_accuracy,
    calculate_completeness,
    calculate_overall_score,
    calculate_relevance,
    evaluate_response,
    normalize_text,
)


def test_normalize_text_removes_stop_words():
    result = normalize_text(
        "Python is a programming language."
    )

    assert result == {"python", "programming", "language"}


def test_normalize_text_is_case_insensitive():
    result = normalize_text(
        "Python PYTHON python"
    )

    assert result == {"python"}


def test_normalize_text_removes_punctuation():
    result = normalize_text(
        "Python, programming, language!"
    )

    assert result == {"python", "programming", "language"}


def test_normalize_text_preserves_hyphenated_terms():
    result = normalize_text(
        "Python is a high-level programming language."
    )

    assert result == {
        "python",
        "high-level",
        "programming",
        "language",
    }


def test_normalize_text_handles_multiple_hyphenated_terms():
    result = normalize_text(
        "Real-time systems use state-of-the-art technology."
    )

    assert result == {
        "real-time",
        "systems",
        "use",
        "state-of-the-art",
        "technology",
    }


def test_normalize_text_empty_text():
    result = normalize_text("")

    assert result == set()


def test_normalize_text_handles_duplicate_words():
    result = normalize_text(
        "Python Python Python programming programming"
    )

    assert result == {
        "python",
        "programming",
    }


def test_normalize_text_handles_numbers():
    result = normalize_text(
        "Python 3 is used with 100 libraries."
    )

    assert result == {
        "python",
        "3",
        "used",
        "100",
        "libraries",
    }


def test_normalize_text_handles_mixed_punctuation():
    result = normalize_text(
        "Python!!! @programming #language $test %example"
    )

    assert result == {
        "python",
        "programming",
        "language",
        "test",
        "example",
    }


def test_normalize_text_handles_whitespace():
    result = normalize_text(
        "  Python   programming\nlanguage\t"
    )

    assert result == {
        "python",
        "programming",
        "language",
    }


def test_normalize_text_handles_unicode_text():
    result = normalize_text(
        "Python café programming"
    )

    assert result == {
        "python",
        "café",
        "programming",
    }


def test_calculate_accuracy():
    result = calculate_accuracy(
        {"python", "programming"},
        {"python", "programming", "language"},
    )

    assert result == 66.67


def test_calculate_accuracy_empty_reference():
    result = calculate_accuracy(
        {"python"},
        set(),
    )

    assert result == 0.0


def test_calculate_relevance():
    result = calculate_relevance(
        {"python", "programming", "language"},
        {"python", "programming"},
    )

    assert result == 66.67


def test_calculate_relevance_empty_response():
    result = calculate_relevance(
        set(),
        {"python"},
    )

    assert result == 0.0


def test_calculate_completeness():
    result = calculate_completeness(
        {"python", "programming"},
        {"python", "programming", "language"},
    )

    assert result == 66.67


def test_calculate_completeness_empty_reference():
    result = calculate_completeness(
        {"python"},
        set(),
    )

    assert result == 0.0


def test_calculate_overall_score():
    result = calculate_overall_score(
        accuracy=66.67,
        relevance=100.0,
        completeness=66.67,
    )

    assert result == 76.67


def test_calculate_overall_score_perfect():
    result = calculate_overall_score(
        accuracy=100.0,
        relevance=100.0,
        completeness=100.0,
    )

    assert result == 100.0


def test_calculate_overall_score_zero():
    result = calculate_overall_score(
        accuracy=0.0,
        relevance=0.0,
        completeness=0.0,
    )

    assert result == 0.0


def test_evaluate_response_passes():
    result = evaluate_response(
        "Python is a programming language.",
        "Python is a high-level programming language.",
    )

    assert result["score"] == 82.5
    assert result["accuracy"] == 75.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 75.0
    assert result["passed"] is True
    assert "python" in result["matched_terms"]


def test_evaluate_response_fails():
    result = evaluate_response(
        "Java is a completely different technology.",
        "Python is a high-level programming language.",
    )

    assert result["score"] == 0.0
    assert result["accuracy"] == 0.0
    assert result["relevance"] == 0.0
    assert result["completeness"] == 0.0
    assert result["passed"] is False


def test_evaluate_response_identifies_missing_terms():
    result = evaluate_response(
        "Python is a programming language.",
        "Python is a high-level programming language.",
    )

    assert "high-level" in result["missing_terms"]


def test_evaluate_response_identifies_matched_terms():
    result = evaluate_response(
        "Python is a programming language.",
        "Python is a high-level programming language.",
    )

    assert "python" in result["matched_terms"]
    assert "programming" in result["matched_terms"]
    assert "language" in result["matched_terms"]


def test_evaluate_response_returns_strong_feedback():
    result = evaluate_response(
        "Python is a programming language.",
        "Python is a high-level programming language.",
    )

    assert result["feedback"] == (
        "Response has strong alignment with the reference answer."
    )


def test_evaluate_response_returns_moderate_feedback():
    result = evaluate_response(
        "Python",
        "Python is a programming language.",
    )

    assert result["feedback"] == (
        "Response has moderate alignment with the reference answer."
    )


def test_evaluate_response_returns_weak_feedback():
    result = evaluate_response(
        "Java",
        "Python is a programming language.",
    )

    assert result["feedback"] == (
        "Response has weak alignment with the reference answer."
    )


def test_evaluate_response_exact_match():
    result = evaluate_response(
        "Python is a programming language.",
        "Python is a programming language.",
    )

    assert result["score"] == 100.0
    assert result["accuracy"] == 100.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 100.0
    assert result["passed"] is True
    assert result["matched_terms"] == [
        "language",
        "programming",
        "python",
    ]
    assert result["missing_terms"] == []


def test_evaluate_response_empty_response():
    result = evaluate_response(
        "",
        "Python is a programming language.",
    )

    assert result["score"] == 0.0
    assert result["accuracy"] == 0.0
    assert result["relevance"] == 0.0
    assert result["completeness"] == 0.0
    assert result["passed"] is False
    assert result["matched_terms"] == []
    assert result["missing_terms"] == [
        "language",
        "programming",
        "python",
    ]


def test_evaluate_response_empty_reference_answer():
    result = evaluate_response(
        "Python is a programming language.",
        "",
    )

    assert result["score"] == 0
    assert result["accuracy"] == 0
    assert result["relevance"] == 0
    assert result["completeness"] == 0
    assert result["passed"] is False
    assert result["matched_terms"] == []
    assert result["missing_terms"] == []
    assert result["feedback"] == "Reference answer is empty."


def test_evaluate_response_whitespace_reference_answer():
    result = evaluate_response(
        "Python is a programming language.",
        "   ",
    )

    assert result["score"] == 0
    assert result["accuracy"] == 0
    assert result["relevance"] == 0
    assert result["completeness"] == 0
    assert result["passed"] is False
    assert result["matched_terms"] == []
    assert result["missing_terms"] == []


def test_evaluate_response_is_case_insensitive():
    result = evaluate_response(
        "PYTHON IS A PROGRAMMING LANGUAGE.",
        "python is a programming language.",
    )

    assert result["score"] == 100.0
    assert result["accuracy"] == 100.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 100.0
    assert result["passed"] is True


def test_evaluate_response_ignores_punctuation():
    result = evaluate_response(
        "Python, is a programming language!",
        "Python is a programming language.",
    )

    assert result["score"] == 100.0
    assert result["accuracy"] == 100.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 100.0
    assert result["passed"] is True


def test_evaluate_response_score_at_strong_alignment_boundary():
    result = evaluate_response(
        "Python programming language",
        "Python programming language",
    )

    assert result["score"] == 100.0
    assert result["passed"] is True


def test_evaluate_response_partial_reference_coverage():
    result = evaluate_response(
        "Python programming",
        "Python programming language",
    )

    assert result["accuracy"] == 66.67
    assert result["relevance"] == 100.0
    assert result["completeness"] == 66.67
    assert result["score"] == 76.67
    assert result["passed"] is True


def test_evaluate_response_single_matching_term():
    result = evaluate_response(
        "Python",
        "Python programming language",
    )

    assert result["accuracy"] == 33.33
    assert result["relevance"] == 100.0
    assert result["completeness"] == 33.33
    assert result["score"] == 53.33
    assert result["passed"] is True


def test_evaluate_response_no_matching_terms():
    result = evaluate_response(
        "Java database",
        "Python programming language",
    )

    assert result["accuracy"] == 0.0
    assert result["relevance"] == 0.0
    assert result["completeness"] == 0.0
    assert result["score"] == 0.0
    assert result["passed"] is False


def test_evaluate_response_extra_terms_reduce_relevance():
    result = evaluate_response(
        "Python programming language unrelated extra information",
        "Python programming language",
    )

    assert result["accuracy"] == 100.0
    assert result["completeness"] == 100.0
    assert result["relevance"] < 100.0
    assert result["score"] < 100.0


def test_evaluate_response_reference_terms_all_present():
    result = evaluate_response(
        "Python programming language",
        "Python programming language",
    )

    assert result["accuracy"] == 100.0
    assert result["completeness"] == 100.0
    assert result["passed"] is True


def test_evaluate_response_handles_duplicate_words():
    result = evaluate_response(
        "Python Python Python programming programming",
        "Python programming language",
    )

    assert result["matched_terms"] == [
        "programming",
        "python",
    ]
    assert result["missing_terms"] == ["language"]
    assert result["accuracy"] == 66.67
    assert result["relevance"] == 100.0
    assert result["completeness"] == 66.67
    assert result["score"] == 76.67


def test_evaluate_response_handles_numbers():
    result = evaluate_response(
        "Python 3 programming",
        "Python 3 programming language",
    )

    assert result["matched_terms"] == [
        "3",
        "programming",
        "python",
    ]
    assert result["missing_terms"] == ["language"]
    assert result["accuracy"] == 75.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 75.0


def test_evaluate_response_handles_whitespace_and_newlines():
    result = evaluate_response(
        "Python   programming\nlanguage",
        "Python programming language",
    )

    assert result["score"] == 100.0
    assert result["accuracy"] == 100.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 100.0


def test_evaluate_response_handles_unicode_text():
    result = evaluate_response(
        "Python café programming",
        "Python café programming language",
    )

    assert "café" in result["matched_terms"]
    assert result["accuracy"] == 75.0
    assert result["relevance"] == 100.0
    assert result["completeness"] == 75.0


def test_evaluate_response_handles_very_long_response():
    response = (
        "Python programming language "
        + "additional information " * 100
    )

    result = evaluate_response(
        response,
        "Python programming language",
    )

    assert result["accuracy"] == 100.0
    assert result["completeness"] == 100.0
    assert result["relevance"] < 100.0
    assert result["score"] < 100.0
    assert result["passed"] is True