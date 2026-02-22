"""
Answer Normalizer Module
Converts raw answer strings into typed, comparable formats
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, Union


class AnswerType(Enum):
    """Types of mathematical answers"""
    FRACTION = "fraction"              # 54584/99000
    DECIMAL = "decimal"                # 8.1, 42.67, 0.129
    INTEGER = "integer"                # 7, -133, 6720
    EXPRESSION = "expression"          # f'(x) = 12x^5, (9/2)x^2 + C
    TEXT = "text"                      # Rational, Irrational
    RANGE = "range"                    # 5 and 6, 8, 9
    SCIENTIFIC_NOTATION = "scientific" # 5 * 10^3
    COORDINATE = "coordinate"          # x = 1.67
    UNKNOWN = "unknown"                # Unable to classify


SUPERSCRIPT_MAP = {
    "\u2070": "0",
    "\u00b9": "1",
    "\u00b2": "2",
    "\u00b3": "3",
    "\u2074": "4",
    "\u2075": "5",
    "\u2076": "6",
    "\u2077": "7",
    "\u2078": "8",
    "\u2079": "9",
    "\u207b": "-",
}


def _strip_math_wrappers(text: str) -> str:
    """
    Remove common surrounding wrappers from extracted math strings.
    """
    text = text.strip()

    # $...$, \( ... \), \[ ... \]
    if text.startswith("$") and text.endswith("$") and len(text) >= 2:
        text = text[1:-1].strip()
    if text.startswith(r"\(") and text.endswith(r"\)") and len(text) >= 4:
        text = text[2:-2].strip()
    if text.startswith(r"\[") and text.endswith(r"\]") and len(text) >= 4:
        text = text[2:-2].strip()

    # Strip one layer of outer braces/parentheses if they wrap the whole value.
    if text.startswith("{") and text.endswith("}") and len(text) >= 2:
        text = text[1:-1].strip()
    if text.startswith("(") and text.endswith(")") and len(text) >= 2:
        inner = text[1:-1].strip()
        if re.match(r"^[^()]+$", inner):
            text = inner

    return text.strip()


@dataclass
class NormalizedAnswer:
    """Normalized answer with type information"""
    value: Any  # Actual normalized value (tuple for fractions, float for decimals, etc.)
    answer_type: AnswerType
    original_text: str
    precision: Optional[int] = None  # For decimals: number of decimal places
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def _is_thousands_formatted_number(text: str) -> bool:
    """
    Check if text is a number using comma thousands separators.

    Examples: '6,561', '28,660.64', '960,844,000'
    Non-examples: '5,6' (range), '1,2,3' (not thousands pattern)
    """
    return bool(re.match(r'^-?\d{1,3}(?:,\d{3})+(?:\.\d+)?$', text))


def detect_answer_type(text: str) -> AnswerType:
    """
    Auto-detect answer type from string

    Args:
        text: Raw answer string

    Returns:
        AnswerType enum value
    """
    text = _strip_math_wrappers(text)

    # Expression patterns (check first - most specific)
    if "f'(x)" in text or "f(x)" in text or "+ C" in text or "·" in text:
        return AnswerType.EXPRESSION

    # Coordinate pattern (x = value, y = value) — decimal form
    if re.match(r'^[a-z]\s*=\s*-?\d+\.?\d*$', text, re.IGNORECASE):
        return AnswerType.COORDINATE

    # Coordinate pattern with fraction value (x = 1/2, x = -3/4)
    if re.match(r'^[a-z]\s*=\s*-?\d+\s*/\s*-?\d+$', text, re.IGNORECASE):
        return AnswerType.COORDINATE

    # Scientific notation (5 * 10^3)
    if re.match(r'^\d+\s*\*\s*10\^', text):
        return AnswerType.SCIENTIFIC_NOTATION

    # Thousands-formatted number (6,561 or 28,660.64) — check before range
    if ',' in text and _is_thousands_formatted_number(text):
        no_comma = text.replace(',', '')
        if '.' in no_comma:
            return AnswerType.DECIMAL
        return AnswerType.INTEGER

    # Range pattern (5 and 6, or 5, 6)
    if " and " in text or re.match(r'^\d+,\s*\d+$', text):
        return AnswerType.RANGE

    # LaTeX fraction pattern
    if re.match(r'^[+-]?\s*\\frac\s*\{-?\d+\}\s*\{-?\d+\}$', text):
        return AnswerType.FRACTION

    # Fraction pattern (numerator/denominator, can have negatives)
    if re.match(r'^\(?\s*-?\d+\s*/\s*-?\d+\s*\)?$', text):
        return AnswerType.FRACTION

    # Decimal pattern (includes negative decimals)
    if re.match(r'^-?\d+\.\d+$', text):
        return AnswerType.DECIMAL

    # Integer pattern (includes negative integers)
    if re.match(r'^-?\d+$', text):
        # Check if it's actually a decimal with .0
        if text.endswith('.0'):
            return AnswerType.DECIMAL
        return AnswerType.INTEGER

    # Text (remaining non-numeric or mostly non-numeric)
    if not any(char.isdigit() for char in text):
        return AnswerType.TEXT

    # If it contains letters and numbers but doesn't match patterns above
    if any(char.isalpha() for char in text):
        # Check if it's text like "Rational" or "Irrational"
        if text.lower() in ['rational', 'irrational', 'r', 'i']:
            return AnswerType.TEXT
        # Otherwise might be an expression we didn't catch
        return AnswerType.EXPRESSION

    return AnswerType.UNKNOWN


def normalize_fraction(text: str) -> NormalizedAnswer:
    """
    Normalize fraction format

    Examples:
        "54584/99000" -> (54584, 99000)
        "-1/-8" -> (-1, -8)
        "3/-9" -> (3, -9)

    Note: Does NOT reduce to simplest form - that's done in comparison
    """
    original_text = text.strip()
    text = _strip_math_wrappers(original_text)

    # Parse pure LaTeX fractions: \frac{a}{b}
    latex_match = re.match(r'^([+-]?)\s*\\frac\s*\{(-?\d+)\}\s*\{(-?\d+)\}$', text)
    if latex_match:
        sign = -1 if latex_match.group(1) == '-' else 1
        numerator = sign * int(latex_match.group(2))
        denominator = int(latex_match.group(3))
        return NormalizedAnswer(
            value=(numerator, denominator),
            answer_type=AnswerType.FRACTION,
            original_text=original_text
        )

    # Strip surrounding parentheses for forms like (1/2)
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()

    match = re.match(r'^(-?\d+)\s*/\s*(-?\d+)$', text)

    if match:
        numerator = int(match.group(1))
        denominator = int(match.group(2))

        return NormalizedAnswer(
            value=(numerator, denominator),
            answer_type=AnswerType.FRACTION,
            original_text=original_text
        )

    # Fallback - couldn't parse
    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.UNKNOWN,
        original_text=original_text,
        metadata={"error": "Could not parse fraction"}
    )


def _normalize_unicode_superscripts(text: str) -> str:
    """
    Convert unicode superscripts to ^-style exponents.
    Example: x³ -> x^3, x⁻² -> x^-2
    """
    superscript_chars = ''.join(SUPERSCRIPT_MAP.keys())

    def repl(match):
        chars = match.group(1)
        converted = ''.join(SUPERSCRIPT_MAP[ch] for ch in chars)
        return f"^{converted}"

    return re.sub(rf'(?<=[A-Za-z0-9\)])([{re.escape(superscript_chars)}]+)', repl, text)


def normalize_decimal(text: str) -> NormalizedAnswer:
    """
    Normalize decimal format

    Examples:
        "8.1" -> 8.1 (precision=1)
        "42.67" -> 42.67 (precision=2)
        "0.129" -> 0.129 (precision=3)
        "28,660.64" -> 28660.64 (precision=2, thousands separator stripped)
    """
    text = text.strip().replace(',', '')  # Strip thousands separators

    # Handle special case of integers with .0
    if text.endswith('.0'):
        text = text[:-2]
        return normalize_integer(text)

    try:
        value = float(text)

        # Count decimal places
        if '.' in text:
            decimal_part = text.split('.')[1]
            precision = len(decimal_part)
        else:
            precision = 0

        return NormalizedAnswer(
            value=value,
            answer_type=AnswerType.DECIMAL,
            original_text=text,
            precision=precision
        )
    except ValueError:
        return NormalizedAnswer(
            value=text,
            answer_type=AnswerType.UNKNOWN,
            original_text=text,
            metadata={"error": "Could not parse decimal"}
        )


def normalize_integer(text: str) -> NormalizedAnswer:
    """
    Normalize integer format

    Examples:
        "6720" -> 6720
        "-133" -> -133
        "6,561" -> 6561 (thousands separator stripped)
    """
    text = text.strip().replace(',', '')  # Strip thousands separators

    try:
        value = int(text)

        return NormalizedAnswer(
            value=value,
            answer_type=AnswerType.INTEGER,
            original_text=text
        )
    except ValueError:
        return NormalizedAnswer(
            value=text,
            answer_type=AnswerType.UNKNOWN,
            original_text=text,
            metadata={"error": "Could not parse integer"}
        )


def normalize_expression(text: str) -> NormalizedAnswer:
    """
    Normalize mathematical expression format

    Normalizations:
        - Standardize spacing: "f'(x)=12x^5" -> "f'(x) = 12x^5"
        - Normalize x^1 -> x, x^0 -> 1 (but only for simple cases)
        - Sort polynomial terms by exponent (descending)
        - Preserve unsimplified fractions like (4/2)

    Examples:
        "f'(x) = 8x^1 + 40x^4" -> "f'(x) = 40x^4 + 8x"
        "(9/2)x^2 + C" -> "(9/2)x^2 + C"
    """
    text = text.strip()
    text = _normalize_unicode_superscripts(text)

    # Normalize common LaTeX expression forms
    # \frac{a}{b} -> (a/b), \cdot -> ·
    text = re.sub(r'\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}', r'(\1/\2)', text)
    text = text.replace('\\cdot', '·').replace('\\times', '·')
    text = text.replace('\\left', '').replace('\\right', '')
    text = text.replace('\\,', '')
    text = re.sub(r'\\(sin|cos|tan|sec|csc|cot|ln|log|exp)\b', r'\1', text)

    # Normalize SQRT notation to unified SQRT(...) form
    # LaTeX: \sqrt{3} -> SQRT(3)
    text = re.sub(r'\\sqrt\s*\{([^}]+)\}', r'SQRT(\1)', text)
    # Unicode: √(3) -> SQRT(3), √3 -> SQRT(3)
    text = re.sub(r'√\(([^)]+)\)', r'SQRT(\1)', text)
    text = re.sub(r'√(\w+)', r'SQRT(\1)', text)
    # Lowercase: sqrt(...) -> SQRT(...)
    text = re.sub(r'\bsqrt\s*\(', 'SQRT(', text)
    # Add implicit multiplication: 4SQRT( -> 4*SQRT(
    text = re.sub(r'(\d)(SQRT)', r'\1*\2', text)

    # Standardize spacing around =
    text = re.sub(r'\s*=\s*', ' = ', text)

    # Normalize x^1 to x (but preserve x^1 in contexts where it matters)
    # Only replace x^1 when it's clearly a standalone term
    text = re.sub(r'([^0-9])x\^1([^0-9])', r'\1x\2', text)
    text = re.sub(r'([^0-9])x\^1$', r'\1x', text)

    # Try to sort polynomial terms only for simple polynomial sums.
    # Skip complex forms (parentheses, multiplication, division, unicode dot)
    # to avoid corrupting expressions like: 4(4x-4)^3 · 4
    if 'f\'(x)' in text or 'f(x)' in text:
        parts = text.split('=', 1)
        if len(parts) == 2:
            left_side = parts[0].strip()
            right_side = parts[1].strip()

            has_complex_ops = any(op in right_side for op in ['(', ')', '*', '/', '·'])
            if has_complex_ops:
                return NormalizedAnswer(
                    value=text,
                    answer_type=AnswerType.EXPRESSION,
                    original_text=text
                )

            # Try to parse and sort terms (simple case)
            # Look for patterns like "8x + 40x^4"
            terms = re.findall(r'[+-]?\s*\d*x\^?\d*', right_side)
            if terms:
                # Sort by exponent (descending)
                def get_exponent(term):
                    match = re.search(r'x\^(\d+)', term)
                    if match:
                        return int(match.group(1))
                    elif 'x' in term:
                        return 1  # x with no exponent is x^1
                    return 0

                try:
                    sorted_terms = sorted(terms, key=get_exponent, reverse=True)
                    # Rebuild the right side
                    sorted_right = ' + '.join(t.strip().lstrip('+').strip() for t in sorted_terms)
                    sorted_right = sorted_right.replace('+ -', '- ')
                    text = f"{left_side} = {sorted_right}"
                except:
                    pass  # Keep original if sorting fails

    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.EXPRESSION,
        original_text=text
    )


def normalize_text(text: str) -> NormalizedAnswer:
    """
    Normalize text answer format

    Examples:
        "Rational" -> "rational"
        "Irrational" -> "irrational"
    """
    text = text.strip().lower()

    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.TEXT,
        original_text=text
    )


def normalize_range(text: str) -> NormalizedAnswer:
    """
    Normalize range format to set

    Examples:
        "5 and 6" -> {5, 6}
        "8, 9" -> {8, 9}
    """
    text = text.strip()

    # Parse "X and Y" format
    if " and " in text:
        parts = text.split(" and ")
        try:
            values = {int(p.strip()) for p in parts}
            return NormalizedAnswer(
                value=values,
                answer_type=AnswerType.RANGE,
                original_text=text
            )
        except ValueError:
            pass

    # Parse "X, Y" format
    if "," in text:
        parts = text.split(",")
        try:
            values = {int(p.strip()) for p in parts}
            return NormalizedAnswer(
                value=values,
                answer_type=AnswerType.RANGE,
                original_text=text
            )
        except ValueError:
            pass

    # Couldn't parse
    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.UNKNOWN,
        original_text=text,
        metadata={"error": "Could not parse range"}
    )


def normalize_scientific_notation(text: str) -> NormalizedAnswer:
    """
    Normalize scientific notation format

    Examples:
        "5 * 10^3" -> (5, 3)
        "9 * 10^(-5)" -> (9, -5)
    """
    text = text.strip()

    # Pattern: coefficient * 10^exponent
    match = re.match(r'^(\d+)\s*\*\s*10\^\(?(-?\d+)\)?$', text)

    if match:
        coefficient = int(match.group(1))
        exponent = int(match.group(2))

        return NormalizedAnswer(
            value=(coefficient, exponent),
            answer_type=AnswerType.SCIENTIFIC_NOTATION,
            original_text=text
        )

    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.UNKNOWN,
        original_text=text,
        metadata={"error": "Could not parse scientific notation"}
    )


def normalize_coordinate(text: str) -> NormalizedAnswer:
    """
    Normalize coordinate format

    Examples:
        "x = 1.67" -> ('x', 1.67, precision=2)
        "y = -2.5" -> ('y', -2.5, precision=1)
        "x = 1/2"  -> ('x', 0.5, precision=2)   (fraction form)
        "x = -3/4" -> ('x', -0.75, precision=2)  (fraction form)
    """
    text = text.strip()

    # Decimal/integer form: x = 1.67
    match = re.match(r'^([a-z])\s*=\s*(-?\d+\.?\d*)$', text, re.IGNORECASE)
    if match:
        variable = match.group(1).lower()
        value_str = match.group(2)

        try:
            value = float(value_str)

            # Count decimal places
            if '.' in value_str:
                decimal_part = value_str.split('.')[1]
                precision = len(decimal_part)
            else:
                precision = 0

            return NormalizedAnswer(
                value=(variable, value),
                answer_type=AnswerType.COORDINATE,
                original_text=text,
                precision=precision
            )
        except ValueError:
            pass

    # Fraction form: x = 1/2, x = -3/4
    frac_match = re.match(r'^([a-z])\s*=\s*(-?\d+)\s*/\s*(-?\d+)$', text, re.IGNORECASE)
    if frac_match:
        variable = frac_match.group(1).lower()
        numerator = int(frac_match.group(2))
        denominator = int(frac_match.group(3))

        if denominator != 0:
            value = numerator / denominator
            # Use precision=2 so fraction coordinates compare with same
            # tolerance as 2-decimal-place expected answers
            return NormalizedAnswer(
                value=(variable, value),
                answer_type=AnswerType.COORDINATE,
                original_text=text,
                precision=2
            )

    return NormalizedAnswer(
        value=text,
        answer_type=AnswerType.UNKNOWN,
        original_text=text,
        metadata={"error": "Could not parse coordinate"}
    )


def normalize_answer(text: str) -> NormalizedAnswer:
    """
    Auto-detect type and normalize answer

    Args:
        text: Raw answer string

    Returns:
        NormalizedAnswer object with typed value
    """
    if not text or not text.strip():
        return NormalizedAnswer(
            value=None,
            answer_type=AnswerType.UNKNOWN,
            original_text=text,
            metadata={"error": "Empty text"}
        )

    # Pre-process Unicode notation so type detection works correctly.
    # 1. Unicode multiplication signs and superscripts (e.g. "9 × 10⁻⁸").
    text = text.replace('×', '*').replace('⋅', '*')
    text = _normalize_unicode_superscripts(text)
    # 2. Unicode radical sign √ and LaTeX \sqrt — normalise to SQRT() now so
    #    type detection sees a known expression pattern rather than UNKNOWN.
    text = re.sub(r'\\sqrt\s*\{([^}]+)\}', r'SQRT(\1)', text)   # \sqrt{3}
    text = re.sub(r'√\(([^)]+)\)', r'SQRT(\1)', text)            # √(3)
    text = re.sub(r'√(\w+)', r'SQRT(\1)', text)                  # √3
    text = re.sub(r'(\d)(SQRT)', r'\1*\2', text)                 # 4SQRT → 4*SQRT

    # Detect type
    answer_type = detect_answer_type(text)

    # Normalize based on type
    if answer_type == AnswerType.FRACTION:
        return normalize_fraction(text)
    elif answer_type == AnswerType.DECIMAL:
        return normalize_decimal(text)
    elif answer_type == AnswerType.INTEGER:
        return normalize_integer(text)
    elif answer_type == AnswerType.EXPRESSION:
        return normalize_expression(text)
    elif answer_type == AnswerType.TEXT:
        return normalize_text(text)
    elif answer_type == AnswerType.RANGE:
        return normalize_range(text)
    elif answer_type == AnswerType.SCIENTIFIC_NOTATION:
        return normalize_scientific_notation(text)
    elif answer_type == AnswerType.COORDINATE:
        return normalize_coordinate(text)
    else:
        return NormalizedAnswer(
            value=text,
            answer_type=AnswerType.UNKNOWN,
            original_text=text
        )


# Quick test
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("54584/99000", AnswerType.FRACTION, (54584, 99000)),
        ("42.67", AnswerType.DECIMAL, 42.67),
        ("-133", AnswerType.INTEGER, -133),
        ("f'(x) = 12x^5", AnswerType.EXPRESSION, None),
        ("Rational", AnswerType.TEXT, "rational"),
        ("5 and 6", AnswerType.RANGE, {5, 6}),
        ("5 * 10^3", AnswerType.SCIENTIFIC_NOTATION, (5, 3)),
        ("x = 1.67", AnswerType.COORDINATE, ('x', 1.67)),
    ]

    print("Testing Answer Normalizer:")
    print("=" * 60)

    for i, (text, expected_type, expected_value) in enumerate(test_cases, 1):
        result = normalize_answer(text)
        type_match = result.answer_type == expected_type
        value_match = expected_value is None or result.value == expected_value
        status = "✓" if type_match and value_match else "✗"

        print(f"\nTest {i}: {status}")
        print(f"  Input: {text}")
        print(f"  Expected Type: {expected_type.value}")
        print(f"  Got Type: {result.answer_type.value}")
        if expected_value is not None:
            print(f"  Expected Value: {expected_value}")
            print(f"  Got Value: {result.value}")
