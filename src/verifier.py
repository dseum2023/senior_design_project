"""
Verifier Module
Orchestrates the full verification pipeline: Extract -> Normalize -> Compare
"""

from dataclasses import dataclass
from typing import Optional

from answer_extractor import extract_answer, ExtractionResult
from answer_normalizer import normalize_answer, NormalizedAnswer
from answer_comparator import compare_answers, ComparisonResult


@dataclass
class VerificationResult:
    """Result of full verification pipeline"""
    # Extraction info
    extracted_answer: Optional[str]
    extraction_method: str
    extraction_confidence: float

    # Normalization info
    extracted_normalized: Optional[NormalizedAnswer]
    expected_normalized: NormalizedAnswer
    alternate_normalized: Optional[NormalizedAnswer]

    # Comparison info
    is_correct: bool
    comparison_confidence: float
    match_type: str
    matched_answer: str  # "main", "alternate", "none"

    # Overall status
    verification_status: str  # "correct", "incorrect", "unable_to_verify", "error"
    error_message: Optional[str]
    details: str


def verify_answer(llm_response: str, expected_answer: str,
                 alternate_answer: Optional[str] = None) -> VerificationResult:
    """
    Full verification pipeline:
    1. Extract answer from LLM response
    2. Normalize extracted, expected, and alternate answers
    3. Compare using type-aware logic
    4. Return comprehensive result

    Args:
        llm_response: Full text response from LLM
        expected_answer: Ground truth answer (from dataset)
        alternate_answer: Optional alternate acceptable answer

    Returns:
        VerificationResult with complete verification information
    """
    try:
        # Step 1: Extract answer from LLM response
        extraction = extract_answer(llm_response)

        if extraction.extracted_answer is None:
            # Extraction failed - unable to verify
            return VerificationResult(
                extracted_answer=None,
                extraction_method=extraction.extraction_method,
                extraction_confidence=0.0,
                extracted_normalized=None,
                expected_normalized=normalize_answer(expected_answer),
                alternate_normalized=normalize_answer(alternate_answer) if alternate_answer else None,
                is_correct=False,
                comparison_confidence=0.0,
                match_type="extraction_failed",
                matched_answer="none",
                verification_status="unable_to_verify",
                error_message="Could not extract answer from LLM response",
                details=f"Tried all extraction methods, none succeeded. Response length: {len(llm_response)} chars"
            )

        # Step 2: Normalize all answers
        extracted_norm = normalize_answer(extraction.extracted_answer)
        expected_norm = normalize_answer(expected_answer)
        alternate_norm = normalize_answer(alternate_answer) if alternate_answer else None

        # Step 3: Compare answers
        comparison = compare_answers(extracted_norm, expected_norm, alternate_norm)

        # Step 4: Build result
        if comparison.is_correct:
            status = "correct"
        else:
            status = "incorrect"

        return VerificationResult(
            extracted_answer=extraction.extracted_answer,
            extraction_method=extraction.extraction_method,
            extraction_confidence=extraction.confidence,
            extracted_normalized=extracted_norm,
            expected_normalized=expected_norm,
            alternate_normalized=alternate_norm,
            is_correct=comparison.is_correct,
            comparison_confidence=comparison.confidence,
            match_type=comparison.match_type,
            matched_answer=comparison.matched_answer,
            verification_status=status,
            error_message=None,
            details=comparison.details
        )

    except Exception as e:
        # Handle unexpected errors
        return VerificationResult(
            extracted_answer=None,
            extraction_method="error",
            extraction_confidence=0.0,
            extracted_normalized=None,
            expected_normalized=normalize_answer(expected_answer),
            alternate_normalized=None,
            is_correct=False,
            comparison_confidence=0.0,
            match_type="error",
            matched_answer="none",
            verification_status="error",
            error_message=str(e),
            details=f"Verification failed with error: {type(e).__name__}: {str(e)}"
        )


# Quick test
if __name__ == "__main__":
    print("Testing Verifier:")
    print("=" * 60)

    # Test 1: Correct answer with FINAL_ANSWER keyword
    print("\nTest 1: Correct Integer Answer")
    llm_resp = "Step 1: Calculate...\nStep 2: Simplify...\nFINAL_ANSWER: -133"
    expected = "-133"
    result = verify_answer(llm_resp, expected)
    print(f"  Status: {result.verification_status}")
    print(f"  Extracted: {result.extracted_answer}")
    print(f"  Method: {result.extraction_method}")
    print(f"  Match: {result.match_type}")
    print(f"  Correct: {'✓' if result.is_correct else '✗'}")

    # Test 2: Incorrect answer
    print("\nTest 2: Incorrect Answer")
    llm_resp = "FINAL_ANSWER: -132"
    expected = "-133"
    result = verify_answer(llm_resp, expected)
    print(f"  Status: {result.verification_status}")
    print(f"  Extracted: {result.extracted_answer}")
    print(f"  Expected: {expected}")
    print(f"  Correct: {'✓' if not result.is_correct else '✗'}")
    print(f"  Details: {result.details}")

    # Test 3: Alternate answer match
    print("\nTest 3: Alternate Answer Match")
    llm_resp = "FINAL_ANSWER: R"
    expected = "Rational"
    alternate = "R"
    result = verify_answer(llm_resp, expected, alternate)
    print(f"  Status: {result.verification_status}")
    print(f"  Matched: {result.matched_answer}")
    print(f"  Correct: {'✓' if result.is_correct and result.matched_answer == 'alternate' else '✗'}")

    # Test 4: Unable to extract
    print("\nTest 4: Unable to Extract")
    llm_resp = "I cannot solve this problem."
    expected = "42"
    result = verify_answer(llm_resp, expected)
    print(f"  Status: {result.verification_status}")
    print(f"  Correct: {'✓' if result.verification_status == 'unable_to_verify' else '✗'}")
    print(f"  Error: {result.error_message}")

    # Test 5: Type mismatch (fraction vs decimal)
    print("\nTest 5: Type Mismatch (Fraction vs Decimal)")
    llm_resp = "FINAL_ANSWER: 0.25"
    expected = "1/4"
    result = verify_answer(llm_resp, expected)
    print(f"  Status: {result.verification_status}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Correct: {'✓' if not result.is_correct and result.match_type == 'type_mismatch' else '✗'}")
    print(f"  Details: {result.details}")
