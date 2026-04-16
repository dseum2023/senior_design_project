"""
Answer Extractor Module
Extracts final answers from verbose LLM responses using multiple strategies
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractionResult:
    """Result of answer extraction from LLM response"""
    extracted_answer: Optional[str]
    extraction_method: str  # "FINAL_ANSWER", "boxed", "keyword", "last_value", "failed"
    confidence: float  # 1.0 for FINAL_ANSWER, 0.8 for boxed, 0.6 for keyword, 0.4 for last_value
    raw_text: str  # Original LLM response


def _clean_extracted_answer(answer: str) -> str:
    """
    Clean extracted answer text from common LaTeX wrapper artifacts.
    """
    answer = answer.strip()

    # Remove surrounding dollar math delimiters
    if answer.startswith("$") and answer.endswith("$") and len(answer) >= 2:
        answer = answer[1:-1].strip()

    # Handle artifacts from patterns like \text{FINAL_ANSWER: } <answer>
    # where generic extraction may capture a leading "}".
    answer = re.sub(r'^\}\s*', '', answer)

    # Strip trailing punctuation artifacts (periods, asterisks) common in LLM output
    answer = answer.rstrip('.*')

    return answer.strip()


def _strip_prose_from_answer(answer: str) -> str:
    """
    Strip English prose from a verbose FINAL_ANSWER extraction.

    Many models (especially Phi) wrap their answer in natural language:
        "504 ways to arrange three items from nine distinct ones"
        "The slope of the tangent line to f(x) at x = 4 is 32"
        "There are 210 different arrangements possible"

    This function extracts the core numeric/math value when prose is detected.
    Returns the original answer unchanged if no prose is found.
    """
    PROSE_WORDS = {
        'the', 'is', 'are', 'was', 'were', 'has', 'have', 'had',
        'ways', 'when', 'where', 'which', 'that', 'this', 'there',
        'from', 'with', 'into', 'about', 'after', 'before',
        'approximately', 'equal', 'equals', 'simply', 'roughly',
        'different', 'possible', 'total', 'items', 'distinct',
        'arrange', 'choose', 'selecting', 'rounded', 'decimal',
        'because', 'since', 'therefore', 'thus', 'hence',
        'calculate', 'calculated', 'result', 'value', 'answer',
        'probability', 'function', 'slope', 'tangent', 'line',
        'arrangements', 'combinations', 'permutations',
    }

    stripped = answer.strip().rstrip('.')

    # Count prose words in the text
    words_lower = stripped.lower().split()
    prose_count = sum(1 for w in words_lower if w in PROSE_WORDS)

    # Only attempt cleanup if there are at least 2 prose words
    if prose_count < 2:
        return answer

    # Pattern: "There are <number> ..." or "There is <number> ..."
    m = re.match(r'^[Tt]here\s+(?:are|is)\s+(?:a\s+total\s+of\s+)?(-?\d+(?:\.\d+)?(?:/\d+)?)', stripped)
    if m:
        return m.group(1)

    # Pattern: "<number> ways/arrangements/combinations/..." (leading number + prose)
    m = re.match(r'^(-?\d+(?:\.\d+)?(?:/\d+)?)\s+[a-zA-Z]', stripped)
    if m:
        return m.group(1)

    # Pattern: "... is [approximately|equal to|simply] <number>" (trailing number after "is")
    m = re.search(r'\bis\s+(?:approximately\s+|equal\s+to\s+|simply\s+|about\s+)?(-?\d+(?:\.\d+)?(?:/\d+)?)\s*(?:when|$)', stripped)
    if m:
        return m.group(1)

    # Pattern: "... is <number>" at end of string
    m = re.search(r'\bis\s+(-?\d+(?:\.\d+)?(?:/\d+)?)\s*$', stripped)
    if m:
        return m.group(1)

    # Pattern: "P(A and B) = 0.201" — math equation, not prose. Leave as-is.
    # (This is caught by the prose_count < 2 guard above in most cases)

    return answer


def _extract_final_answer_keyword(text: str) -> Optional[str]:
    """
    Extract answer using FINAL_ANSWER: keyword format (PRIMARY method)

    Pattern: FINAL_ANSWER: [answer]
    Case-insensitive
    """
    patterns = [
        # LaTeX text wrapper variant:
        # \text{FINAL_ANSWER: } \frac{4}{7}x^7 + C
        r'\\text\{FINAL_ANSWER:\s*\}\s*(.+?)(?:\n|$)',
        # Standard variant:
        r'FINAL_ANSWER:\s*(.+?)(?:\n|$)',
        # "FINAL_ANSWER is <answer>" variant (e.g. Phi-style):
        r'FINAL_ANSWER\s+is\s+(.+?)(?:\n|$)',
        # "FINAL_ANSWER = <answer>" or "FINAL_ANSWER=<answer>" variant:
        r'FINAL_ANSWER\s*=\s*(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            answer = _clean_extracted_answer(match.group(1))
            if answer:
                return answer

    return None


def _extract_boxed(text: str) -> Optional[str]:
    """
    Extract answer from LaTeX \\boxed{} notation (FALLBACK 1)

    Pattern: \\boxed{answer}
    Handles nested braces if needed
    """
    # Robust parse for nested braces, e.g. \boxed{\frac{4x^7}{7} + C}
    marker = r'\boxed{'
    boxed_contents = []
    start_idx = 0

    while True:
        marker_idx = text.find(marker, start_idx)
        if marker_idx == -1:
            break

        content_start = marker_idx + len(marker)
        depth = 1
        i = content_start

        while i < len(text):
            char = text[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    content = text[content_start:i].strip()
                    if content:
                        boxed_contents.append(content)
                    start_idx = i + 1
                    break
            i += 1
        else:
            # Unbalanced braces; stop parsing boxed sections.
            break

    if boxed_contents:
        # Return the last boxed answer (typically the final answer)
        return _clean_extracted_answer(boxed_contents[-1])

    # Fallback for simple non-nested forms
    pattern = r'\\boxed\{([^}\n]+)\}'
    matches = re.findall(pattern, text)
    if matches:
        return _clean_extracted_answer(matches[-1].strip())

    return None


def _extract_keyword_patterns(text: str) -> Optional[str]:
    """
    Extract answer using common keyword patterns (FALLBACK 2)

    Patterns: "Answer:", "The answer is", "Therefore"
    Takes last occurrence if multiple found
    """
    patterns = [
        r'Answer:\s*(.+?)(?:\n|$)',
        r'The answer is\s*(.+?)(?:\n|$)',
        r'Therefore[,:]?\s*(.+?)(?:\n|$)',
    ]

    all_matches = []

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        all_matches.extend(matches)

    if all_matches:
        # Return the last match
        return all_matches[-1].strip()

    return None


def _extract_last_value(text: str) -> Optional[str]:
    """
    Extract last mathematical value in text (FALLBACK 3)

    Looks for (in priority order):
    - Fractions (e.g., 1/4) — most specific pattern
    - Numbers (integers, decimals, negative) — prefer plain numeric values
    - Coordinate expressions (e.g., x = 1.67) — last resort, as these often
      appear in LLM working/intermediate steps rather than the final answer
    """
    # Try to find fractions first (most specific)
    fraction_pattern = r'-?\d+/-?\d+'
    fraction_matches = re.findall(fraction_pattern, text)
    if fraction_matches:
        return fraction_matches[-1].strip()

    # Try to find decimals or integers
    number_pattern = r'-?\d+\.?\d*'
    number_matches = re.findall(number_pattern, text)
    if number_matches:
        valid_numbers = [n for n in number_matches if len(n) > 0]
        if valid_numbers:
            return valid_numbers[-1].strip()

    # Last resort: coordinate pattern (x = value)
    # Deprioritized because LLM working often contains intermediate variable
    # assignments like "X = 92" or "u = 13.3" that are not the final answer
    coord_pattern = r'[a-z]\s*=\s*-?\d+\.?\d*'
    coord_matches = re.findall(coord_pattern, text, re.IGNORECASE)
    if coord_matches:
        return coord_matches[-1].strip()

    return None


def extract_answer(llm_response: str) -> ExtractionResult:
    """
    Extract final answer from LLM response using multiple strategies

    Strategy priority:
    1. FINAL_ANSWER: keyword (confidence=1.0)
    2. LaTeX \\boxed{} (confidence=0.8)
    3. Common keywords (confidence=0.6)
    4. Last value (confidence=0.4)

    Args:
        llm_response: Full text response from LLM

    Returns:
        ExtractionResult with extracted answer and metadata
    """
    if not llm_response or not llm_response.strip():
        return ExtractionResult(
            extracted_answer=None,
            extraction_method="failed",
            confidence=0.0,
            raw_text=llm_response
        )

    # Strategy 1: FINAL_ANSWER keyword (PRIMARY)
    answer = _extract_final_answer_keyword(llm_response)
    if answer:
        cleaned = _strip_prose_from_answer(answer)
        return ExtractionResult(
            extracted_answer=cleaned,
            extraction_method="FINAL_ANSWER",
            confidence=1.0 if cleaned == answer else 0.9,
            raw_text=llm_response
        )

    # Strategy 2: LaTeX boxed notation (FALLBACK 1)
    answer = _extract_boxed(llm_response)
    if answer:
        return ExtractionResult(
            extracted_answer=answer,
            extraction_method="boxed",
            confidence=0.8,
            raw_text=llm_response
        )

    # Strategy 3: Common keywords (FALLBACK 2)
    answer = _extract_keyword_patterns(llm_response)
    if answer:
        return ExtractionResult(
            extracted_answer=answer,
            extraction_method="keyword",
            confidence=0.6,
            raw_text=llm_response
        )

    # Strategy 4: Last mathematical value (FALLBACK 3)
    answer = _extract_last_value(llm_response)
    if answer:
        return ExtractionResult(
            extracted_answer=answer,
            extraction_method="last_value",
            confidence=0.4,
            raw_text=llm_response
        )

    # All strategies failed
    return ExtractionResult(
        extracted_answer=None,
        extraction_method="failed",
        confidence=0.0,
        raw_text=llm_response
    )


# Quick test
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Step 1...\nStep 2...\nFINAL_ANSWER: 42.67", "42.67", "FINAL_ANSWER"),
        ("Therefore:\n\\boxed{-133}", "-133", "boxed"),
        ("The answer is 8.1", "8.1", "keyword"),
        ("...calculating gives us 54584/99000 as the result.", "54584/99000", "last_value"),
    ]

    print("Testing Answer Extractor:")
    print("=" * 60)

    for i, (response, expected, method) in enumerate(test_cases, 1):
        result = extract_answer(response)
        status = "✓" if result.extracted_answer == expected and result.extraction_method == method else "✗"
        print(f"\nTest {i}: {status}")
        print(f"  Expected: {expected} ({method})")
        print(f"  Got: {result.extracted_answer} ({result.extraction_method})")
        print(f"  Confidence: {result.confidence}")
