"""
Answer Comparator Module
Type-aware comparison of normalized answers
"""

import re
import math
from math import gcd
from dataclasses import dataclass
from typing import Optional

from answer_normalizer import NormalizedAnswer, AnswerType


@dataclass
class ComparisonResult:
    """Result of comparing two answers"""
    is_correct: bool
    confidence: float  # 0.0 to 1.0
    match_type: str  # "exact", "equivalent", "tolerance", "no_match", "type_mismatch"
    details: str  # Human-readable explanation
    matched_answer: str = "none"  # "main", "alternate", or "none"


def compare_fractions(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two fractions by reducing to lowest terms

    Examples:
        1/4 vs 2/8 -> MATCH (both reduce to 1/4)
        -1/-8 vs 1/8 -> MATCH (both reduce to 1/8)
        1/4 vs 1/3 -> NO MATCH
    """
    n1, d1 = ans1.value
    n2, d2 = ans2.value

    # Reduce both to lowest terms using GCD
    g1 = gcd(abs(n1), abs(d1))
    g2 = gcd(abs(n2), abs(d2))

    n1_reduced = n1 // g1
    d1_reduced = d1 // g1
    n2_reduced = n2 // g2
    d2_reduced = d2 // g2

    # Handle negative denominators: move sign to numerator
    if d1_reduced < 0:
        n1_reduced = -n1_reduced
        d1_reduced = -d1_reduced
    if d2_reduced < 0:
        n2_reduced = -n2_reduced
        d2_reduced = -d2_reduced

    # Compare reduced forms
    if n1_reduced == n2_reduced and d1_reduced == d2_reduced:
        match_type = "exact" if (n1 == n2 and d1 == d2) else "equivalent"
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type=match_type,
            details=f"Fractions equivalent: {n1}/{d1} = {n2}/{d2} (reduced: {n1_reduced}/{d1_reduced})"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Fractions not equal: {n1_reduced}/{d1_reduced} ≠ {n2_reduced}/{d2_reduced}"
        )


def compare_decimals(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two decimals with tolerance based on least precision.

    Tolerance = 0.5 * (10 ** -precision)
    Examples:
        precision=1 -> tolerance=0.05
        precision=2 -> tolerance=0.005
        precision=3 -> tolerance=0.0005
    """
    val1 = ans1.value
    val2 = ans2.value

    # Determine tolerance based on the less precise decimal representation.
    # This allows equivalent rounded values (e.g., 125.6636 vs 125.66) to match.
    precision = min(ans1.precision or 2, ans2.precision or 2)
    tolerance = 0.5 * (10 ** -precision)

    diff = abs(val1 - val2)

    if diff == 0:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Exact decimal match: {val1} = {val2}"
        )
    elif diff <= tolerance:
        # Linear confidence falloff
        confidence = 1.0 - (diff / tolerance)
        return ComparisonResult(
            is_correct=True,
            confidence=confidence,
            match_type="tolerance",
            details=f"Decimals within tolerance: |{val1} - {val2}| = {diff:.6f} <= {tolerance}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Decimals differ: |{val1} - {val2}| = {diff:.6f} > {tolerance}"
        )


def compare_fraction_and_decimal(
    fraction_ans: NormalizedAnswer, decimal_ans: NormalizedAnswer
) -> ComparisonResult:
    """
    Compare fraction vs decimal using decimal precision tolerance.

    Example:
        40/3 vs 13.33 -> MATCH (within 0.005 for precision=2)
    """
    if fraction_ans.answer_type != AnswerType.FRACTION or decimal_ans.answer_type != AnswerType.DECIMAL:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details=f"Type mismatch: {fraction_ans.answer_type.value} vs {decimal_ans.answer_type.value}",
        )

    num, den = fraction_ans.value
    if den == 0:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details="Invalid fraction denominator 0",
        )

    frac_value = num / den
    dec_value = float(decimal_ans.value)
    precision = decimal_ans.precision if decimal_ans.precision is not None else 2
    tolerance = 0.5 * (10 ** -precision)
    diff = abs(frac_value - dec_value)

    if diff <= tolerance:
        match_type = "exact" if diff == 0 else "tolerance"
        confidence = 1.0 if diff == 0 else (1.0 - (diff / tolerance))
        return ComparisonResult(
            is_correct=True,
            confidence=confidence,
            match_type=match_type,
            details=f"Fraction/decimal match: {num}/{den} ~= {dec_value} within tolerance {tolerance}",
        )

    return ComparisonResult(
        is_correct=False,
        confidence=1.0,
        match_type="no_match",
        details=f"Fraction/decimal differ: |{frac_value} - {dec_value}| = {diff:.6f} > {tolerance}",
    )


def compare_integers(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two integers (exact match only)

    Examples:
        6720 vs 6720 -> MATCH
        -133 vs -133 -> MATCH
        7 vs 8 -> NO MATCH
    """
    if ans1.value == ans2.value:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Integer exact match: {ans1.value} = {ans2.value}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Integers not equal: {ans1.value} ≠ {ans2.value}"
        )


def compare_expressions(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two mathematical expressions

    Comparison is whitespace-insensitive after normalization

    Examples:
        "f'(x) = 12x^5" vs "f'(x)=12x^5" -> MATCH
        "f'(x) = 8x + 40x^4" vs "f'(x) = 40x^4 + 8x" -> MATCH (both normalized)
    """
    expr1 = str(ans1.value).strip()
    expr2 = str(ans2.value).strip()

    def _strip_assignment_label(expr: str) -> tuple[str, bool]:
        """
        Strip simple assignment labels from expressions.

        Examples:
            f'(x)=15x^4 -> 15x^4
            y=3x+1 -> 3x+1
            x+1=0 -> unchanged (not treated as a label assignment)
        """
        expr_clean = re.sub(r'\s+', '', expr)
        if '=' not in expr_clean:
            return expr_clean, False

        left, right = expr_clean.split('=', 1)

        # Simple variable/function label, optionally with prime(s) and arguments
        #   x, y, f(x), f'(x), g''(t)
        label_pattern = r"^[a-zA-Z]\w*(?:'+)?(?:\([^=+\-*/^]+\))?$"
        if re.match(label_pattern, left):
            return right, True

        return expr_clean, False

    def _to_evaluable(expr: str) -> Optional[str]:
        """
        Convert a math expression string into a Python-evaluable expression.
        Returns None when unsupported tokens are present.
        """
        expr = (
            expr.replace("·", "*")
            .replace("⋅", "*")
            .replace("×", "*")
            .replace("?", "*")
            .replace("−", "-")
        )
        expr = re.sub(r"\s+", "", expr)
        expr = expr.replace("^", "**")

        # Normalize common sign combinations.
        while "+-" in expr or "--" in expr or "-+" in expr:
            expr = expr.replace("+-", "-").replace("--", "+").replace("-+", "-")

        # Allow only a strict safe subset.
        if not re.match(r"^[0-9a-zA-Z+\-*/().*]+$", expr):
            return None

        # Insert implicit multiplication:
        # 2x -> 2*x, 2(x+1) -> 2*(x+1), )x -> )*x, )( -> )*(
        expr = re.sub(r"(?<=[0-9a-zA-Z\)])(?=\()", "*", expr)
        expr = re.sub(r"(?<=[0-9\)])(?=[a-zA-Z])", "*", expr)
        expr = re.sub(r"(?<=[a-zA-Z\)])(?=\d)", "*", expr)

        return expr

    def _to_evaluable_safe(expr: str) -> Optional[str]:
        """
        Convert a math expression to a Python-evaluable form with trig/log support.
        """
        expr = (
            expr.replace("·", "*")
            .replace("⋅", "*")
            .replace("×", "*")
            .replace("Â·", "*")
            .replace("â‹…", "*")
            .replace("Ã—", "*")
            .replace("?", "*")
            .replace("−", "-")
            .replace("âˆ’", "-")
        )
        expr = re.sub(r"\bln\s*\(", "log(", expr)
        expr = re.sub(r"\s+", "", expr)
        expr = expr.replace("^", "**")

        while "+-" in expr or "--" in expr or "-+" in expr:
            expr = expr.replace("+-", "-").replace("--", "+").replace("-+", "-")

        if not re.match(r"^[0-9a-zA-Z_+\-*/().]+$", expr):
            return None

        # Implicit multiplication:
        # 2x -> 2*x, 2(x+1) -> 2*(x+1), x(x+1) -> x*(x+1), )x -> )*x
        # Keep function calls like sin(x), cos(x), log(x) intact.
        expr = re.sub(r"(?<=[0-9\)])(?=\()", "*", expr)
        expr = re.sub(r"(?<=\b[a-zA-Z])(?=\()", "*", expr)
        expr = re.sub(r"(?<=[0-9\)])(?=[a-zA-Z])", "*", expr)
        expr = re.sub(r"(?<=[a-zA-Z\)])(?=\d)", "*", expr)

        return expr

    def _numeric_equivalent(expr_a: str, expr_b: str) -> bool:
        """
        Numeric fallback for equivalent algebraic forms (e.g., expanded/factored).
        """
        eval_a = _to_evaluable_safe(expr_a)
        eval_b = _to_evaluable_safe(expr_b)
        if eval_a is None or eval_b is None:
            return False

        function_names = {"sin", "cos", "tan", "sec", "csc", "cot", "log", "exp",
                          "sqrt", "SQRT"}
        tokens_a = set(re.findall(r"[A-Za-z_]+", eval_a))
        tokens_b = set(re.findall(r"[A-Za-z_]+", eval_b))
        variables = sorted((tokens_a.union(tokens_b)) - function_names)

        test_points = [-2.5, -1.7, -0.9, -0.3, 0.4, 1.1, 2.2]
        checked = 0
        safe_globals = {
            "__builtins__": {},
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "exp": math.exp,
            "sec": lambda x: 1.0 / math.cos(x),
            "csc": lambda x: 1.0 / math.sin(x),
            "cot": lambda x: 1.0 / math.tan(x),
            "abs": abs,
            "sqrt": math.sqrt,
            "SQRT": math.sqrt,
        }

        for p in test_points:
            env = {var: p for var in variables}
            try:
                val_a = eval(eval_a, safe_globals, env)
                val_b = eval(eval_b, safe_globals, env)
            except Exception:
                continue

            checked += 1
            tolerance = max(1e-8, 1e-6 * max(1.0, abs(val_a), abs(val_b)))
            if abs(val_a - val_b) > tolerance:
                return False

        return checked >= 3

    # Remove all whitespace for comparison
    expr1_clean = re.sub(r'\s+', '', expr1)
    expr2_clean = re.sub(r'\s+', '', expr2)

    if expr1_clean == expr2_clean:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Expression match: {expr1}"
        )

    # Fallback: allow equivalent expressions when one/both sides include
    # assignment-style labels such as f'(x)=, y=, x=
    expr1_rhs, stripped1 = _strip_assignment_label(expr1)
    expr2_rhs, stripped2 = _strip_assignment_label(expr2)
    if (stripped1 or stripped2) and expr1_rhs == expr2_rhs:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="equivalent",
            details=f"Expression match after removing assignment label: '{expr1_rhs}'"
        )

    # Numeric fallback for algebraically equivalent forms.
    if _numeric_equivalent(expr1_rhs, expr2_rhs):
        return ComparisonResult(
            is_correct=True,
            confidence=0.95,
            match_type="equivalent",
            details="Expression match by numeric equivalence check"
        )

    return ComparisonResult(
        is_correct=False,
        confidence=1.0,
        match_type="no_match",
        details=f"Expression mismatch: '{expr1}' vs '{expr2}'"
    )


def compare_coordinate_and_scalar(
    coordinate_ans: NormalizedAnswer, scalar_ans: NormalizedAnswer
) -> ComparisonResult:
    """
    Compare coordinate answer (e.g., x = 1.67) against scalar-only value (e.g., 1.67).
    """
    if coordinate_ans.answer_type != AnswerType.COORDINATE:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details="Internal error: first argument is not coordinate"
        )

    var_name, coord_value = coordinate_ans.value

    scalar_value = None
    coord_precision = coordinate_ans.precision if coordinate_ans.precision is not None else 2
    scalar_precision = scalar_ans.precision if scalar_ans.precision is not None else 2

    if scalar_ans.answer_type == AnswerType.INTEGER:
        scalar_value = float(scalar_ans.value)
        scalar_precision = 0
    elif scalar_ans.answer_type == AnswerType.DECIMAL:
        scalar_value = float(scalar_ans.value)
    elif scalar_ans.answer_type == AnswerType.FRACTION:
        num, den = scalar_ans.value
        if den == 0:
            return ComparisonResult(
                is_correct=False,
                confidence=1.0,
                match_type="no_match",
                details="Invalid fraction denominator 0 in scalar answer"
            )
        scalar_value = num / den
        # Use coordinate precision when comparing exact fraction to rounded coordinate.
        scalar_precision = coord_precision
    elif scalar_ans.answer_type == AnswerType.SCIENTIFIC_NOTATION:
        coef, exp = scalar_ans.value
        scalar_value = float(coef * (10 ** exp))
        scalar_precision = coord_precision
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details=f"Type mismatch: coordinate vs {scalar_ans.answer_type.value}"
        )

    precision = max(coord_precision, scalar_precision)
    tolerance = 0.5 * (10 ** -precision)
    diff = abs(coord_value - scalar_value)

    if diff <= tolerance:
        match_type = "exact" if diff == 0 else "tolerance"
        confidence = 1.0 if diff == 0 else (1.0 - (diff / tolerance))
        return ComparisonResult(
            is_correct=True,
            confidence=confidence,
            match_type=match_type,
            details=f"Coordinate/scalar match: {var_name}={coord_value} and {scalar_value}"
        )

    return ComparisonResult(
        is_correct=False,
        confidence=1.0,
        match_type="no_match",
        details=f"Coordinate/scalar values differ: {var_name}={coord_value} vs {scalar_value}"
    )


def compare_text(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two text answers (case-insensitive, already lowercased in normalization)

    Examples:
        "rational" vs "rational" -> MATCH
        "Rational" vs "rational" -> MATCH (normalized)
        "rational" vs "irrational" -> NO MATCH
    """
    if ans1.value == ans2.value:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Text match: {ans1.value}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Text mismatch: '{ans1.value}' vs '{ans2.value}'"
        )


def compare_ranges(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two ranges (sets of values, order-independent)

    Examples:
        {5, 6} vs {5, 6} -> MATCH
        {5, 6} vs {6, 5} -> MATCH (set equality)
        {8, 9} vs {8, 10} -> NO MATCH
    """
    if ans1.value == ans2.value:  # Set equality
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Range match: {ans1.value}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Range mismatch: {ans1.value} vs {ans2.value}"
        )


def compare_scientific_notation(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two scientific notation values by numeric value

    Examples:
        5 * 10^3 vs 5 * 10^3 -> MATCH (exact)
        5 * 10^3 vs 50 * 10^2 -> MATCH (equivalent, both equal 5000)
    """
    coef1, exp1 = ans1.value
    coef2, exp2 = ans2.value

    val1 = coef1 * (10 ** exp1)
    val2 = coef2 * (10 ** exp2)

    if val1 == val2:
        match_type = "exact" if (coef1 == coef2 and exp1 == exp2) else "equivalent"
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type=match_type,
            details=f"Scientific notation match: {coef1}*10^{exp1} = {coef2}*10^{exp2} = {val1}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Scientific notation mismatch: {coef1}*10^{exp1} ({val1}) vs {coef2}*10^{exp2} ({val2})"
        )


def compare_coordinates(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two coordinate values (x = value, y = value)

    Examples:
        x = 1.67 vs x = 1.67 -> MATCH
        x = 1.67 vs x = 1.66 -> NO MATCH (outside tolerance)
        x = 1.67 vs y = 1.67 -> NO MATCH (different variables)
    """
    var1, val1 = ans1.value
    var2, val2 = ans2.value

    if var1 != var2:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Different variables: {var1} vs {var2}"
        )

    # Compare values using decimal comparison logic
    precision = max(ans1.precision or 2, ans2.precision or 2)
    tolerance = 0.5 * (10 ** -precision)
    diff = abs(val1 - val2)

    if diff <= tolerance:
        match_type = "exact" if diff == 0 else "tolerance"
        confidence = 1.0 if diff == 0 else (1.0 - (diff / tolerance))
        return ComparisonResult(
            is_correct=True,
            confidence=confidence,
            match_type=match_type,
            details=f"Coordinate match: {var1} = {val1}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Coordinate values differ: {var1}={val1} vs {var2}={val2}"
        )


def compare_integer_and_decimal(
    integer_ans: NormalizedAnswer, decimal_ans: NormalizedAnswer
) -> ComparisonResult:
    """
    Compare integer vs decimal by converting integer to float.

    Examples:
        6 vs 6.0 -> MATCH (exact)
        6 vs 6.01 -> check within tolerance
        6 vs 7.0 -> NO MATCH
    """
    int_value = float(integer_ans.value)
    dec_value = float(decimal_ans.value)
    precision = decimal_ans.precision if decimal_ans.precision is not None else 2
    tolerance = 0.5 * (10 ** -precision)
    diff = abs(int_value - dec_value)

    if diff == 0:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="exact",
            details=f"Integer/decimal exact match: {integer_ans.value} = {dec_value}"
        )
    elif diff <= tolerance:
        confidence = 1.0 - (diff / tolerance)
        return ComparisonResult(
            is_correct=True,
            confidence=confidence,
            match_type="tolerance",
            details=f"Integer/decimal within tolerance: |{int_value} - {dec_value}| = {diff:.6f} <= {tolerance}"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Integer/decimal differ: {integer_ans.value} vs {dec_value}"
        )


def compare_integer_and_fraction(
    integer_ans: NormalizedAnswer, fraction_ans: NormalizedAnswer
) -> ComparisonResult:
    """
    Compare integer vs fraction by reducing the fraction.

    Examples:
        2 vs 6/3 -> MATCH (6/3 reduces to 2/1)
        2 vs 2/1 -> MATCH
        2 vs 7/3 -> NO MATCH
    """
    int_value = integer_ans.value
    num, den = fraction_ans.value

    if den == 0:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details="Invalid fraction denominator 0"
        )

    g = gcd(abs(num), abs(den))
    num_reduced = num // g
    den_reduced = den // g

    if den_reduced < 0:
        num_reduced = -num_reduced
        den_reduced = -den_reduced

    if den_reduced == 1 and num_reduced == int_value:
        return ComparisonResult(
            is_correct=True,
            confidence=1.0,
            match_type="equivalent",
            details=f"Integer/fraction match: {int_value} = {num}/{den} (reduced: {num_reduced}/{den_reduced})"
        )
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="no_match",
            details=f"Integer/fraction differ: {int_value} vs {num}/{den} (reduced: {num_reduced}/{den_reduced})"
        )


def compare_expression_and_scalar(
    expression_ans: NormalizedAnswer, scalar_ans: NormalizedAnswer
) -> ComparisonResult:
    """
    Compare an expression against a scalar (integer or decimal) by evaluating
    the expression numerically and checking if it equals the scalar value.

    Handles cases like f'(x) = 1x^0 vs 1 (since x^0 = 1 for all x).

    Only matches when the expression evaluates to a constant equal to the scalar.
    """
    expr = str(expression_ans.value).strip()

    # Strip assignment label (e.g., f'(x) = ...)
    expr_clean = re.sub(r'\s+', '', expr)
    if '=' in expr_clean:
        left, right = expr_clean.split('=', 1)
        label_pattern = r"^[a-zA-Z]\w*(?:'+)?(?:\([^=+\-*/^]+\))?$"
        if re.match(label_pattern, left):
            expr_clean = right

    # Build evaluable form
    expr_eval = (
        expr_clean.replace("·", "*")
        .replace("⋅", "*")
        .replace("×", "*")
        .replace("?", "*")
        .replace("−", "-")
    )
    expr_eval = expr_eval.replace("^", "**")

    while "+-" in expr_eval or "--" in expr_eval or "-+" in expr_eval:
        expr_eval = expr_eval.replace("+-", "-").replace("--", "+").replace("-+", "-")

    if not re.match(r"^[0-9a-zA-Z+\-*/().*]+$", expr_eval):
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details=f"Cannot evaluate expression for scalar comparison: {expr}"
        )

    # Insert implicit multiplication
    expr_eval = re.sub(r"(?<=[0-9a-zA-Z\)])(?=\()", "*", expr_eval)
    expr_eval = re.sub(r"(?<=[0-9\)])(?=[a-zA-Z])", "*", expr_eval)
    expr_eval = re.sub(r"(?<=[a-zA-Z\)])(?=\d)", "*", expr_eval)

    # Get scalar value
    if scalar_ans.answer_type == AnswerType.INTEGER:
        scalar_value = float(scalar_ans.value)
    elif scalar_ans.answer_type == AnswerType.DECIMAL:
        scalar_value = float(scalar_ans.value)
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details=f"Type mismatch: expression vs {scalar_ans.answer_type.value}"
        )

    # Evaluate expression at multiple test points to check if it's a constant
    safe_globals = {
        "__builtins__": {},
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "exp": math.exp,
        "sqrt": math.sqrt, "SQRT": math.sqrt, "abs": abs,
    }
    test_points = [-2.5, -0.7, 0.4, 1.3, 2.8]
    tokens = set(re.findall(r"[A-Za-z_]+", expr_eval))
    function_names = {"sin", "cos", "tan", "log", "exp", "sqrt", "SQRT", "abs",
                      "sec", "csc", "cot"}
    variables = sorted(tokens - function_names)

    checked = 0
    for p in test_points:
        env = {var: p for var in variables}
        try:
            val = eval(expr_eval, safe_globals, env)
        except Exception:
            continue
        checked += 1
        tolerance = max(1e-8, 1e-6 * max(1.0, abs(scalar_value)))
        if abs(val - scalar_value) > tolerance:
            return ComparisonResult(
                is_correct=False,
                confidence=1.0,
                match_type="no_match",
                details=f"Expression evaluates to {val} at test point, not {scalar_value}"
            )

    if checked >= 3:
        return ComparisonResult(
            is_correct=True,
            confidence=0.95,
            match_type="equivalent",
            details=f"Expression '{expr}' evaluates to {scalar_value} (constant)"
        )

    return ComparisonResult(
        is_correct=False,
        confidence=1.0,
        match_type="type_mismatch",
        details=f"Could not evaluate expression '{expr}' for scalar comparison"
    )


def _compare_single(ans1: NormalizedAnswer, ans2: NormalizedAnswer) -> ComparisonResult:
    """
    Compare two normalized answers

    CRITICAL: Type must match exactly (fraction ≠ decimal)
    """
    # CRITICAL: Type must match
    if ans1.answer_type != ans2.answer_type:
        # Allow coordinate value vs scalar-only value (e.g., "x = 1.67" vs "1.67")
        scalar_types = {
            AnswerType.INTEGER,
            AnswerType.DECIMAL,
            AnswerType.FRACTION,
            AnswerType.SCIENTIFIC_NOTATION,
        }
        if ans1.answer_type == AnswerType.COORDINATE and ans2.answer_type in scalar_types:
            return compare_coordinate_and_scalar(ans1, ans2)
        if ans2.answer_type == AnswerType.COORDINATE and ans1.answer_type in scalar_types:
            return compare_coordinate_and_scalar(ans2, ans1)
        if ans1.answer_type == AnswerType.FRACTION and ans2.answer_type == AnswerType.DECIMAL:
            return compare_fraction_and_decimal(ans1, ans2)
        if ans2.answer_type == AnswerType.FRACTION and ans1.answer_type == AnswerType.DECIMAL:
            return compare_fraction_and_decimal(ans2, ans1)

        # INTEGER <-> DECIMAL
        if ans1.answer_type == AnswerType.INTEGER and ans2.answer_type == AnswerType.DECIMAL:
            return compare_integer_and_decimal(ans1, ans2)
        if ans2.answer_type == AnswerType.INTEGER and ans1.answer_type == AnswerType.DECIMAL:
            return compare_integer_and_decimal(ans2, ans1)

        # INTEGER <-> FRACTION
        if ans1.answer_type == AnswerType.INTEGER and ans2.answer_type == AnswerType.FRACTION:
            return compare_integer_and_fraction(ans1, ans2)
        if ans2.answer_type == AnswerType.INTEGER and ans1.answer_type == AnswerType.FRACTION:
            return compare_integer_and_fraction(ans2, ans1)

        # EXPRESSION vs scalar (INTEGER/DECIMAL)
        scalar_numeric = {AnswerType.INTEGER, AnswerType.DECIMAL}
        if ans1.answer_type == AnswerType.EXPRESSION and ans2.answer_type in scalar_numeric:
            return compare_expression_and_scalar(ans1, ans2)
        if ans2.answer_type == AnswerType.EXPRESSION and ans1.answer_type in scalar_numeric:
            return compare_expression_and_scalar(ans2, ans1)

        return ComparisonResult(
            is_correct=False,
            confidence=1.0,
            match_type="type_mismatch",
            details=f"Type mismatch: {ans1.answer_type.value} vs {ans2.answer_type.value}",
            matched_answer="none"
        )

    # Dispatch to type-specific comparison
    if ans1.answer_type == AnswerType.FRACTION:
        return compare_fractions(ans1, ans2)
    elif ans1.answer_type == AnswerType.DECIMAL:
        return compare_decimals(ans1, ans2)
    elif ans1.answer_type == AnswerType.INTEGER:
        return compare_integers(ans1, ans2)
    elif ans1.answer_type == AnswerType.EXPRESSION:
        return compare_expressions(ans1, ans2)
    elif ans1.answer_type == AnswerType.TEXT:
        return compare_text(ans1, ans2)
    elif ans1.answer_type == AnswerType.RANGE:
        return compare_ranges(ans1, ans2)
    elif ans1.answer_type == AnswerType.SCIENTIFIC_NOTATION:
        return compare_scientific_notation(ans1, ans2)
    elif ans1.answer_type == AnswerType.COORDINATE:
        return compare_coordinates(ans1, ans2)
    else:
        return ComparisonResult(
            is_correct=False,
            confidence=0.0,
            match_type="unknown",
            details=f"Unknown answer type: {ans1.answer_type.value}"
        )


def compare_answers(extracted: NormalizedAnswer, expected: NormalizedAnswer,
                   alternate: Optional[NormalizedAnswer] = None) -> ComparisonResult:
    """
    Compare extracted answer against expected (and optionally alternate)

    Args:
        extracted: Answer extracted from LLM response
        expected: Expected ground truth answer
        alternate: Optional alternate acceptable answer

    Returns:
        ComparisonResult with match information
    """
    # Try main answer first
    result = _compare_single(extracted, expected)
    if result.is_correct:
        result.matched_answer = "main"
        return result

    # Try alternate if exists
    if alternate is not None:
        result_alt = _compare_single(extracted, alternate)
        if result_alt.is_correct:
            result_alt.matched_answer = "alternate"
            return result_alt

    # No match
    result.matched_answer = "none"
    return result


# Quick test
if __name__ == "__main__":
    from answer_normalizer import normalize_answer

    print("Testing Answer Comparator:")
    print("=" * 60)

    # Test 1: Fraction vs Decimal (TYPE MISMATCH - critical)
    print("\nTest 1: Fraction vs Decimal (should be TYPE MISMATCH)")
    frac = normalize_answer("1/4")
    dec = normalize_answer("0.25")
    result = compare_answers(frac, dec)
    print(f"  Result: {'✓' if not result.is_correct and result.match_type == 'type_mismatch' else '✗'}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Details: {result.details}")

    # Test 2: Equivalent fractions
    print("\nTest 2: Equivalent Fractions (1/4 vs 2/8)")
    frac1 = normalize_answer("1/4")
    frac2 = normalize_answer("2/8")
    result = compare_answers(frac1, frac2)
    print(f"  Result: {'✓' if result.is_correct else '✗'}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Details: {result.details}")

    # Test 3: Decimal tolerance
    print("\nTest 3: Decimal Tolerance (8.1 vs 8.06)")
    dec1 = normalize_answer("8.1")
    dec2 = normalize_answer("8.06")
    result = compare_answers(dec1, dec2)
    print(f"  Result: {'✓' if result.is_correct else '✗'}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Details: {result.details}")

    # Test 4: Integer exact match
    print("\nTest 4: Integer Exact Match (-133 vs -133)")
    int1 = normalize_answer("-133")
    int2 = normalize_answer("-133")
    result = compare_answers(int1, int2)
    print(f"  Result: {'✓' if result.is_correct else '✗'}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Details: {result.details}")

    # Test 5: Text case-insensitive
    print("\nTest 5: Text Case-Insensitive (Rational vs rational)")
    text1 = normalize_answer("Rational")
    text2 = normalize_answer("rational")
    result = compare_answers(text1, text2)
    print(f"  Result: {'✓' if result.is_correct else '✗'}")
    print(f"  Match Type: {result.match_type}")
    print(f"  Details: {result.details}")
