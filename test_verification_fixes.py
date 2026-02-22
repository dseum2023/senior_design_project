"""
Tests for verification fixes targeting questions that were incorrectly marked
as incorrect in the result files.

Covers the four bug categories fixed:
  1. Comma-formatted thousands separators (grade 8)
  2. SQRT notation equivalence (grade 8)
  3. Coordinate answers with fraction values (calculus)
  4. Trailing-period extraction artifact (calculus/Phi)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from verifier import verify_answer
from answer_normalizer import normalize_answer, AnswerType
from answer_extractor import extract_answer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(label, llm_response, expected_answer, alternate_answer=None,
           expect_correct=True, expect_incorrect=False):
    result = verify_answer(llm_response, expected_answer, alternate_answer)
    if expect_correct:
        assert result.is_correct, (
            f"FAIL [{label}]: expected CORRECT but got {result.verification_status}. "
            f"extracted={result.extracted_answer!r}, expected={expected_answer!r}, "
            f"match={result.match_type}, details={result.details}"
        )
    if expect_incorrect:
        assert not result.is_correct, (
            f"FAIL [{label}]: expected INCORRECT but got CORRECT. "
            f"extracted={result.extracted_answer!r}, expected={expected_answer!r}"
        )
    return result


# ===========================================================================
# 1. Comma-formatted thousands separators
# ===========================================================================

def test_comma_integer_exact():
    """6,561 (expected) must match 6561 (LLM answer)."""
    # Grade 8 Q193: (3^2)^4
    _check("Q193 comma-int", "FINAL_ANSWER: 6561", "6,561")

def test_comma_integer_large():
    """8,000,000,000 must match 8000000000."""
    # Grade 8 Q287
    _check("Q287 large comma-int", "FINAL_ANSWER: 8000000000", "8,000,000,000")

def test_comma_integer_5300():
    """5,300 must match 5300."""
    # Grade 8 Q295
    _check("Q295 comma-int 5300", "FINAL_ANSWER: 5300", "5,300")

def test_comma_decimal_tolerance():
    """28,660.64 must match 28660.6442 within 2dp tolerance."""
    # Grade 8 Q300
    _check("Q300 comma-decimal", "FINAL_ANSWER: 28660.6442", "28,660.64")

def test_comma_decimal_exact():
    """6,449.24 must match 6449.24043 within 2dp tolerance."""
    # Grade 8 Q314
    _check("Q314 comma-decimal", "FINAL_ANSWER: 6449.24043", "6,449.24")

def test_comma_not_range():
    """Comma number should NOT be treated as a range."""
    norm = normalize_answer("6,561")
    assert norm.answer_type == AnswerType.INTEGER, (
        f"6,561 should be INTEGER, got {norm.answer_type}"
    )
    assert norm.value == 6561

def test_comma_wrong_answer_stays_incorrect():
    """A genuinely wrong comma-number answer must not be accepted."""
    # 8000/3 ≈ 2666 ≠ 1750
    _check("comma wrong answer", "FINAL_ANSWER: 8000/3", "1,750",
           expect_correct=False, expect_incorrect=True)


# ===========================================================================
# 2. SQRT notation equivalence
# ===========================================================================

def test_sqrt_latex_vs_ascii():
    """4\\sqrt{3} (LLM LaTeX) must match 4*SQRT(3) (expected ASCII)."""
    # Grade 8 Q107
    _check("Q107 sqrt latex", "FINAL_ANSWER: 4\\sqrt{3}", "4*SQRT(3)")

def test_sqrt_unicode_vs_ascii():
    """4√3 (Unicode) must match 4*SQRT(3)."""
    # Grade 8 Q107 alternative notation
    _check("Q107 sqrt unicode", "FINAL_ANSWER: 4√3", "4*SQRT(3)")

def test_sqrt_latex_14():
    """2\\sqrt{14} must match 2*SQRT(14)."""
    # Grade 8 Q108
    _check("Q108 sqrt 14", "FINAL_ANSWER: 2\\sqrt{14}", "2*SQRT(14)")

def test_sqrt_latex_7():
    """2\\sqrt{7} must match 2*SQRT(7)."""
    # Grade 8 Q109
    _check("Q109 sqrt 7", "FINAL_ANSWER: 2\\sqrt{7}", "2*SQRT(7)")

def test_sqrt_numeric_equivalence():
    """sqrt(3)*5 (numeric form) must match 5*SQRT(3) via numeric check."""
    _check("sqrt commuted", "FINAL_ANSWER: sqrt(3)*5", "5*SQRT(3)")

def test_sqrt_wrong_radicand_stays_incorrect():
    """2*SQRT(7) must NOT match 2*SQRT(14) — different radicands."""
    _check("sqrt wrong radicand", "FINAL_ANSWER: 2\\sqrt{7}", "2*SQRT(14)",
           expect_correct=False, expect_incorrect=True)


# ===========================================================================
# 3. Coordinate answers with fraction values
# ===========================================================================

def test_coordinate_fraction_half():
    """x = 1/2 must match x = 0.5."""
    # Calculus Q6 (Phi/Gemma)
    _check("Q6 coord x=1/2", "FINAL_ANSWER: x = 1/2", "x = 0.5")

def test_coordinate_fraction_nine_tenths():
    """x = 9/10 must match x = 0.9."""
    # Calculus Q20
    _check("Q20 coord x=9/10", "FINAL_ANSWER: x = 9/10", "x = 0.9")

def test_coordinate_fraction_neg_three_quarters():
    """x = -3/4 must match x = -0.75."""
    # Calculus Q35
    _check("Q35 coord x=-3/4", "FINAL_ANSWER: x = -3/4", "x = -0.75")

def test_coordinate_fraction_three_quarters():
    """x = 3/4 must match x = 0.75."""
    # Calculus Q54
    _check("Q54 coord x=3/4", "FINAL_ANSWER: x = 3/4", "x = 0.75")

def test_coordinate_fraction_neg_one_third():
    """x = -1/3 must match x = -0.33 (within 2dp tolerance)."""
    # Calculus Q98
    _check("Q98 coord x=-1/3", "FINAL_ANSWER: x = -1/3", "x = -0.33")

def test_coordinate_fraction_one_sixth():
    """x = 1/6 must match x = 0.17 (within 2dp tolerance)."""
    # Calculus Q134
    _check("Q134 coord x=1/6", "FINAL_ANSWER: x = 1/6", "x = 0.17")

def test_coordinate_fraction_wrong_stays_incorrect():
    """x = 3/4 must NOT match x = 0.5 — different values."""
    _check("coord wrong fraction", "FINAL_ANSWER: x = 3/4", "x = 0.5",
           expect_correct=False, expect_incorrect=True)


# ===========================================================================
# 4. Trailing period extraction artifact
# ===========================================================================

def test_trailing_period_fraction():
    """15/2. (with trailing period) must match 7.5."""
    # Calculus Q53 (Phi)
    _check("Q53 trailing period fraction", "FINAL_ANSWER: 15/2.", "7.5")

def test_trailing_period_neg_fraction():
    """-3/4. (with trailing period) must match x = -0.75 as a coordinate."""
    # The extractor strips '.' → '-3/4' → fraction type.
    # Expected 'x = -0.75' is coordinate; fraction scalar vs coordinate is handled.
    result = extract_answer("FINAL_ANSWER: -3/4.")
    assert result.extracted_answer == "-3/4", (
        f"Expected '-3/4' after stripping '.', got {result.extracted_answer!r}"
    )

def test_trailing_period_doesnt_strip_internal():
    """A decimal like 3.14 must not have its decimal point stripped."""
    result = extract_answer("FINAL_ANSWER: 3.14")
    assert result.extracted_answer == "3.14", (
        f"3.14 internal dot must be preserved, got {result.extracted_answer!r}"
    )


# ===========================================================================
# 5. Scientific notation with Unicode (grade 8 Q265)
# ===========================================================================

def test_scientific_notation_unicode():
    """9 × 10⁻⁸ (Unicode) must match 9 * 10^(-8) (ASCII)."""
    _check("Q265 sci notation unicode", "FINAL_ANSWER: 9 × 10⁻⁸", "9 * 10^(-8)")


# ===========================================================================
# 6. No false positives — genuinely wrong answers stay incorrect
# ===========================================================================

def test_no_false_positive_different_integer():
    _check("different integers", "FINAL_ANSWER: 42", "43",
           expect_correct=False, expect_incorrect=True)

def test_no_false_positive_different_fraction():
    _check("different fractions", "FINAL_ANSWER: 1/3", "1/4",
           expect_correct=False, expect_incorrect=True)

def test_no_false_positive_wrong_sqrt():
    _check("wrong sqrt", "FINAL_ANSWER: 3*SQRT(2)", "3*SQRT(3)",
           expect_correct=False, expect_incorrect=True)

def test_no_false_positive_wrong_coordinate():
    _check("wrong coord decimal", "FINAL_ANSWER: x = 0.6", "x = 0.5",
           expect_correct=False, expect_incorrect=True)

def test_no_false_positive_repeating_decimal_as_decimal():
    """LLM computed 0.551*35=19.285 instead of converting to fraction 54584/99000."""
    _check("Q1 wrong repeating decimal", "FINAL_ANSWER: 19.285", "54584/99000",
           expect_correct=False, expect_incorrect=True)


# ===========================================================================
# Runner
# ===========================================================================

if __name__ == "__main__":
    import traceback

    tests = [
        # Comma numbers
        test_comma_integer_exact,
        test_comma_integer_large,
        test_comma_integer_5300,
        test_comma_decimal_tolerance,
        test_comma_decimal_exact,
        test_comma_not_range,
        test_comma_wrong_answer_stays_incorrect,
        # SQRT
        test_sqrt_latex_vs_ascii,
        test_sqrt_unicode_vs_ascii,
        test_sqrt_latex_14,
        test_sqrt_latex_7,
        test_sqrt_numeric_equivalence,
        test_sqrt_wrong_radicand_stays_incorrect,
        # Coordinate fractions
        test_coordinate_fraction_half,
        test_coordinate_fraction_nine_tenths,
        test_coordinate_fraction_neg_three_quarters,
        test_coordinate_fraction_three_quarters,
        test_coordinate_fraction_neg_one_third,
        test_coordinate_fraction_one_sixth,
        test_coordinate_fraction_wrong_stays_incorrect,
        # Trailing period
        test_trailing_period_fraction,
        test_trailing_period_neg_fraction,
        test_trailing_period_doesnt_strip_internal,
        # Scientific notation Unicode
        test_scientific_notation_unicode,
        # No false positives
        test_no_false_positive_different_integer,
        test_no_false_positive_different_fraction,
        test_no_false_positive_wrong_sqrt,
        test_no_false_positive_wrong_coordinate,
        test_no_false_positive_repeating_decimal_as_decimal,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests.")
    sys.exit(0 if failed == 0 else 1)
