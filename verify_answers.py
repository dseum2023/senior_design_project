#!/usr/bin/env python3
"""Verify all question-answer pairs in the XML datasets."""

import xml.etree.ElementTree as ET
from math import factorial, sqrt, pi
from fractions import Fraction
import re

errors = []

def check(dataset, row_id, problem, expected, issue):
    errors.append({
        "dataset": dataset,
        "id": row_id,
        "problem": problem,
        "expected_answer": expected,
        "issue": issue
    })

def parse_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()
    rows = []
    for row in root.findall("row"):
        rows.append({
            "id": row.get("id"),
            "directions": row.find("Directions").text or "",
            "problem": row.find("Problem").text or "",
            "solution": row.find("Solution").text or "",
            "alternate": row.find("AlternateSolution").text or "",
        })
    return rows

# ===========================
# CALCULUS 1 VERIFICATION
# ===========================
def verify_calculus1():
    rows = parse_xml("calculus1_problems.xml")
    print(f"Checking {len(rows)} Calculus I problems...")

    for r in rows:
        d = r["directions"]
        p = r["problem"]
        s = r["solution"]
        rid = r["id"]

        # --- Power rule derivatives ---
        if "power rule" in d.lower():
            m = re.match(r"f\(x\)\s*=\s*(\d+)x\^(\d+)", p)
            if m:
                coef = int(m.group(1))
                n = int(m.group(2))
                expected = f"f'(x) = {coef*n}x^{n-1}"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Power rule: expected '{expected}', got '{s}'")

        # --- Sum rule derivatives ---
        if d == "Find the derivative.":
            m = re.match(r"f\(x\)\s*=\s*(-?\d+)x\^(\d+)\s*\+\s*(-?\d+)x\^(\d+)\s*\+\s*(-?\d+)", p)
            if m:
                c1, n1, c2, n2, const = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                expected = f"f'(x) = {c1*n1}x^{n1-1} + {c2*n2}x^{n2-1}"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Sum rule: expected '{expected}', got '{s}'")

        # --- Chain rule derivatives ---
        if "chain rule" in d.lower():
            m = re.match(r"f\(x\)\s*=\s*\((\d+)x\s*\+\s*(-?\d+)\)\^(\d+)", p)
            if m:
                inner_coef = int(m.group(1))
                const = int(m.group(2))
                n = int(m.group(3))
                expected = f"f'(x) = {n}({inner_coef}x + {const})^{n-1} · {inner_coef}"
                # Normalize spaces for comparison
                s_norm = s.replace(" ", "").replace("·", "·")
                e_norm = expected.replace(" ", "").replace("·", "·")
                if s_norm != e_norm:
                    check("calculus1", rid, p, s, f"Chain rule: expected '{expected}', got '{s}'")

        # --- Quotient rule ---
        if "quotient rule" in d.lower():
            m = re.match(r"f\(x\)\s*=\s*x\^(\d+)\s*/\s*x\^(\d+)", p)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                if a == b:
                    expected = "f'(x) = 0"
                else:
                    expected = f"f'(x) = {a-b}x^{a-b-1}"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Quotient rule: expected '{expected}', got '{s}'")

        # --- Product rule ---
        if "product rule" in d.lower():
            m = re.match(r"f\(x\)\s*=\s*x\^(\d+)\s*·\s*sin\(x\)", p)
            if m:
                a = int(m.group(1))
                expected = f"f'(x) = {a}x^{a-1}·sin(x) + x^{a}·cos(x)"
                s_norm = s.replace(" ", "")
                e_norm = expected.replace(" ", "")
                if s_norm != e_norm:
                    check("calculus1", rid, p, s, f"Product rule: expected '{expected}', got '{s}'")

        # --- Indefinite integrals (power rule) ---
        if "indefinite integral" in d.lower() or d == "Find the indefinite integral.":
            # Power rule integrals
            m = re.match(r"integral of (\d+)x\^(\d+) dx", p)
            if m:
                coef = int(m.group(1))
                n = int(m.group(2))
                expected = f"({coef}/{n+1})x^{n+1} + C"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Integral power rule: expected '{expected}', got '{s}'")

            # Trig integrals
            m = re.match(r"integral of (\d+)(sin|cos)\(x\) dx", p)
            if m:
                coef = int(m.group(1))
                func = m.group(2)
                if func == "sin":
                    expected = f"-{coef}cos(x) + C"
                else:
                    expected = f"{coef}sin(x) + C"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Trig integral: expected '{expected}', got '{s}'")

        # --- Definite integrals ---
        if d == "Evaluate the definite integral.":
            m = re.match(r"integral from (\d+) to (\d+) of (\d+)x\^(\d+) dx", p)
            if m:
                a, b, coef, n = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                upper = coef * (b**(n+1)) / (n+1)
                lower = coef * (a**(n+1)) / (n+1)
                result = round(upper - lower, 2)
                try:
                    given = float(s)
                    if abs(given - result) > 0.01:
                        check("calculus1", rid, p, s, f"Definite integral: expected {result}, got {s}")
                except ValueError:
                    check("calculus1", rid, p, s, f"Definite integral: could not parse answer '{s}'")

        # --- Limits ---
        if "limit" in d.lower():
            # Polynomial limits
            m = re.match(r"lim\(x->(-?\d+)\)\s*\[(-?\d+)x\^2\s*\+\s*(-?\d+)x\s*\+\s*(-?\d+)\]", p)
            if m:
                x_val = int(m.group(1))
                a, b, c = int(m.group(2)), int(m.group(3)), int(m.group(4))
                result = a * x_val**2 + b * x_val + c
                try:
                    given = float(s) if '.' in s else int(s)
                    if given != result:
                        check("calculus1", rid, p, s, f"Polynomial limit: expected {result}, got {s}")
                except ValueError:
                    pass

            # Limits at infinity (same degree)
            m = re.match(r"lim\(x->infinity\)\s*\[(\d+)x\^3\s*/\s*(\d+)x\^3\]", p)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                result = round(a/b, 2)
                try:
                    given = float(s)
                    if abs(given - result) > 0.001:
                        check("calculus1", rid, p, s, f"Limit at infinity: expected {result}, got {s}")
                except ValueError:
                    pass

            # Limits at infinity (lower degree numerator)
            m = re.match(r"lim\(x->infinity\)\s*\[(\d+)x\^2\s*/\s*(\d+)x\^3\]", p)
            if m:
                if s != "0":
                    check("calculus1", rid, p, s, f"Limit at infinity (lower degree): expected 0, got {s}")

            # Factoring limits
            m = re.match(r"lim\(x->(\d+)\)\s*\[\(x\^2\s*-\s*(\d+)\)\s*/\s*\(x\s*-\s*(\d+)\)\]", p)
            if m:
                a = int(m.group(1))
                a_sq = int(m.group(2))
                a_check = int(m.group(3))
                if a == a_check and a_sq == a**2:
                    result = 2 * a
                    try:
                        given = int(s)
                        if given != result:
                            check("calculus1", rid, p, s, f"Factoring limit: expected {result}, got {s}")
                    except ValueError:
                        pass

        # --- Critical points ---
        if "critical point" in d.lower():
            m = re.match(r"Find the critical points of f\(x\)\s*=\s*(\d+)x\^2\s*\+\s*(-?\d+)x\s*\+\s*(-?\d+)", p)
            if m:
                a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
                x_crit = round(-b / (2 * a), 2)
                expected = f"x = {x_crit}"
                if s.replace(" ", "") != expected.replace(" ", ""):
                    check("calculus1", rid, p, s, f"Critical points: expected '{expected}', got '{s}'")

        # --- Tangent line slope ---
        if "tangent" in d.lower():
            m = re.match(r"Find the slope of the tangent line to f\(x\)\s*=\s*(\d+)x\^2\s*at\s*x\s*=\s*(-?\d+)", p)
            if m:
                a = int(m.group(1))
                x0 = int(m.group(2))
                slope = 2 * a * x0
                try:
                    given = int(s)
                    if given != slope:
                        check("calculus1", rid, p, s, f"Tangent slope: expected {slope}, got {s}")
                except ValueError:
                    pass

        # --- Related rates ---
        if "related rates" in d.lower() or "rate of change" in p.lower():
            m = re.match(r"The radius of a circle is increasing at (\d+) cm/s.*r = (\d+) cm", p)
            if m:
                rate = int(m.group(1))
                radius = int(m.group(2))
                result = round(2 * 3.14159 * radius * rate, 2)
                try:
                    given = float(s)
                    if abs(given - result) > 0.01:
                        check("calculus1", rid, p, s, f"Related rates: expected {result}, got {s}")
                except ValueError:
                    pass


# ===========================
# PROBABILITY & STATS VERIFICATION
# ===========================
def verify_prob_stats():
    rows = parse_xml("advanced_probability_statistics_problems.xml")
    print(f"Checking {len(rows)} Probability & Statistics problems...")

    negative_prob_count = 0
    prob_sum_off_count = 0

    for r in rows:
        d = r["directions"]
        p = r["problem"]
        s = r["solution"]
        rid = r["id"]

        # --- Expected Value ---
        if "expected value" in d.lower():
            # Parse probabilities - strip trailing periods from values
            pairs = re.findall(r"P\(X=(\d+)\)\s*=\s*(-?[\d.]+)", p)
            pairs = [(x[0], x[1].rstrip('.')) for x in pairs]
            if pairs:
                outcomes = [int(x[0]) for x in pairs]
                probs = [float(x[1]) for x in pairs]

                # Check for negative probabilities
                neg_probs = [(o, pr) for o, pr in zip(outcomes, probs) if pr < 0]
                if neg_probs:
                    negative_prob_count += 1
                    check("prob_stats", rid, p, s,
                          f"NEGATIVE PROBABILITY: {', '.join([f'P(X={o})={pr}' for o, pr in neg_probs])} — probabilities cannot be negative")
                    continue

                # Check probabilities > 1
                high_probs = [(o, pr) for o, pr in zip(outcomes, probs) if pr > 1]
                if high_probs:
                    check("prob_stats", rid, p, s,
                          f"PROBABILITY > 1: {', '.join([f'P(X={o})={pr}' for o, pr in high_probs])}")
                    continue

                # Check if probabilities sum to 1
                prob_sum = sum(probs)
                if abs(prob_sum - 1.0) > 0.02:
                    prob_sum_off_count += 1
                    check("prob_stats", rid, p, s,
                          f"Probabilities sum to {prob_sum:.4f}, not 1.0")
                    continue

                # Verify the expected value calculation
                exp_val = sum(o * pr for o, pr in zip(outcomes, probs))
                expected = round(exp_val, 2)
                try:
                    given = float(s)
                    if abs(given - expected) > 0.02:
                        check("prob_stats", rid, p, s,
                              f"Expected value: calculated {expected}, given {s}")
                except ValueError:
                    pass

        # --- Variance ---
        if "variance" in d.lower():
            pairs = re.findall(r"P\(X=(\d+)\)\s*=\s*([\d.]+)", p)
            pairs = [(x[0], x[1].rstrip('.')) for x in pairs]
            if pairs:
                outcomes = [int(x[0]) for x in pairs]
                probs = [float(x[1]) for x in pairs]

                prob_sum = sum(probs)
                if abs(prob_sum - 1.0) > 0.02:
                    check("prob_stats", rid, p, s, f"Variance problem: probabilities sum to {prob_sum:.4f}")
                    continue

                exp_val = sum(o * pr for o, pr in zip(outcomes, probs))
                variance = sum(pr * (o - exp_val)**2 for o, pr in zip(outcomes, probs))
                expected = round(variance, 2)
                try:
                    given = float(s)
                    if abs(given - expected) > 0.02:
                        check("prob_stats", rid, p, s,
                              f"Variance: calculated {expected}, given {s}")
                except ValueError:
                    pass

        # --- Z-score ---
        if "z-score" in d.lower():
            m = re.match(r"For X ~ N\(mean=(-?\d+),\s*std_dev=(\d+)\),\s*find the z-score when X = (-?\d+)", p)
            if m:
                mu, sigma, x = int(m.group(1)), int(m.group(2)), int(m.group(3))
                z = round((x - mu) / sigma, 2)
                try:
                    given = float(s)
                    if abs(given - z) > 0.01:
                        check("prob_stats", rid, p, s, f"Z-score: expected {z}, got {s}")
                except ValueError:
                    pass

        # --- Binomial coefficient ---
        if "binomial coefficient" in p.lower():
            m = re.match(r"Calculate the binomial coefficient C\((\d+),(\d+)\)", p)
            if m:
                n, k = int(m.group(1)), int(m.group(2))
                result = factorial(n) // (factorial(k) * factorial(n - k))
                try:
                    given = int(s)
                    if given != result:
                        check("prob_stats", rid, p, s, f"Binomial coefficient: expected {result}, got {s}")
                except ValueError:
                    pass

        # --- Combinations ---
        if "choose" in p.lower():
            m = re.match(r"How many ways can you choose (\d+) items from (\d+) distinct items", p)
            if m:
                r_val, n = int(m.group(1)), int(m.group(2))
                result = factorial(n) // (factorial(r_val) * factorial(n - r_val))
                try:
                    given = int(s)
                    if given != result:
                        check("prob_stats", rid, p, s, f"Combinations: expected {result}, got {s}")
                except ValueError:
                    pass

        # --- Permutations ---
        if "arrange" in p.lower():
            m = re.match(r"How many ways can you arrange (\d+) items from (\d+) distinct items", p)
            if m:
                r_val, n = int(m.group(1)), int(m.group(2))
                result = factorial(n) // factorial(n - r_val)
                try:
                    given = int(s)
                    if given != result:
                        check("prob_stats", rid, p, s, f"Permutations: expected {result}, got {s}")
                except ValueError:
                    pass

        # --- Conditional probability ---
        if "P(A and B)" in p:
            m = re.match(r"If P\(A\) = ([\d.]+) and P\(B\|A\) = ([\d.]+), find P\(A and B\)", p)
            if m:
                pa, pb_given_a = float(m.group(1)), float(m.group(2))
                result = round(pa * pb_given_a, 3)
                try:
                    given = float(s)
                    if abs(given - result) > 0.001:
                        check("prob_stats", rid, p, s, f"Conditional probability: expected {result}, got {s}")
                except ValueError:
                    pass

        # --- Simple probability ---
        if "probability of selecting" in p.lower():
            m = re.match(r"A bag contains (\d+) balls, (\d+) of which are red", p)
            if m:
                total, favorable = int(m.group(1)), int(m.group(2))
                result = round(favorable / total, 3)
                try:
                    given = float(s)
                    if abs(given - result) > 0.001:
                        check("prob_stats", rid, p, s, f"Simple probability: expected {result}, got {s}")
                except ValueError:
                    pass

    print(f"  -> Found {negative_prob_count} problems with negative probabilities")
    print(f"  -> Found {prob_sum_off_count} problems where probabilities don't sum to 1")


# ===========================
# GRADE 8 VERIFICATION
# ===========================
def verify_grade8():
    rows = parse_xml("grade_8_math_problems.xml")
    print(f"Checking {len(rows)} Grade 8 problems...")

    for r in rows:
        d = r["directions"]
        p = r["problem"]
        s = r["solution"]
        rid = r["id"]

        # --- Repeating decimals to fractions ---
        if "repeating decimal" in d.lower():
            # Parse the decimal: format like 0.551(35) means 0.5513535...
            # Or 5.7(4) means 5.7444...
            m = re.match(r"(-?)([\d]*)\.([\d]*)\(([\d]+)\)", p)
            if m:
                sign = -1 if m.group(1) == '-' else 1
                integer_part = m.group(2) if m.group(2) else "0"
                non_rep = m.group(3)  # non-repeating decimal digits
                rep = m.group(4)      # repeating part

                # Convert to fraction:
                # x = integer.non_rep(rep_rep_rep...)
                # Multiply to shift non-repeating part out: 10^len(non_rep) * x
                # Multiply to shift one repeat out: 10^(len(non_rep)+len(rep)) * x
                # Subtract to eliminate repeating part

                all_digits = non_rep + rep
                len_nr = len(non_rep)
                len_r = len(rep)

                # The number = integer_part + (non_rep_digits followed by repeating rep) as decimal
                # Formula: fraction = (all_digits_number - non_rep_number) / (10^(len_nr+len_r) - 10^len_nr)
                # Then add the integer part

                nr_num = int(non_rep) if non_rep else 0
                all_num = int(all_digits)

                denom = 10**(len_nr + len_r) - 10**len_nr
                numer = all_num - nr_num

                # Add integer part
                int_part = int(integer_part)
                total_numer = sign * (int_part * denom + numer)

                # Parse expected answer
                frac_m = re.match(r"(-?\d+)/(\d+)", s)
                if frac_m:
                    exp_num = int(frac_m.group(1))
                    exp_den = int(frac_m.group(2))

                    # Compare as fractions
                    f_expected = Fraction(exp_num, exp_den)
                    f_computed = Fraction(total_numer, denom)

                    if f_expected != f_computed:
                        check("grade8", rid, p, s,
                              f"Repeating decimal: computed {f_computed} ({total_numer}/{denom}), expected {exp_num}/{exp_den} ({f_expected})")

        # --- Rational/Irrational ---
        if "rational" in d.lower() and "irrational" in d.lower():
            # SQRT problems
            m = re.match(r"SQRT\((\d+)\)", p)
            if m:
                val = int(m.group(1))
                sqrt_val = sqrt(val)
                is_perfect_square = sqrt_val == int(sqrt_val)
                expected = "Rational" if is_perfect_square else "Irrational"
                if s != expected:
                    check("grade8", rid, p, s, f"Rational/Irrational: SQRT({val}) should be {expected}, got {s}")

            # Pi problems
            if "π" in p:
                # Any non-zero multiple of pi is irrational
                if s != "Irrational":
                    check("grade8", rid, p, s, f"Pi multiple should be Irrational, got {s}")

            # Fraction problems
            frac_m = re.match(r"(\d+)/(\d+)$", p)
            if frac_m:
                if s != "Rational":
                    check("grade8", rid, p, s, f"Fraction should be Rational, got {s}")

            # Repeating decimals (with parentheses) are rational
            if re.match(r"[\d.]+\(\d+\)", p):
                if s != "Rational":
                    check("grade8", rid, p, s, f"Repeating decimal should be Rational, got {s}")

            # Non-repeating non-terminating decimals (ending in ......) are irrational
            if p.endswith("......"):
                if s != "Irrational":
                    check("grade8", rid, p, s, f"Non-repeating decimal should be Irrational, got {s}")

            # Pure integers are rational
            if re.match(r"^\d+$", p):
                if s != "Rational":
                    check("grade8", rid, p, s, f"Integer should be Rational, got {s}")

            # Terminating decimals (no parentheses, no ...) are rational
            if re.match(r"^\d+\.\d+$", p):
                if s != "Rational":
                    check("grade8", rid, p, s, f"Terminating decimal should be Rational, got {s}")

        # --- Square root closer to ---
        if "closer to" in d.lower():
            m = re.match(r"Is SQRT\((\d+)\) closer to (\d+) or (\d+)\?", p)
            if m:
                val = int(m.group(1))
                opt1, opt2 = int(m.group(2)), int(m.group(3))
                sqrt_val = sqrt(val)
                dist1 = abs(sqrt_val - opt1)
                dist2 = abs(sqrt_val - opt2)
                expected = str(opt1) if dist1 < dist2 else str(opt2)
                if s != expected:
                    check("grade8", rid, p, s,
                          f"SQRT({val}) = {sqrt_val:.4f}, closer to {expected}, but answer says {s}")


# ===========================
# RUN ALL
# ===========================
if __name__ == "__main__":
    print("=" * 70)
    print("DATASET ANSWER VERIFICATION")
    print("=" * 70)

    verify_calculus1()
    verify_prob_stats()
    verify_grade8()

    print("\n" + "=" * 70)
    print(f"TOTAL ERRORS FOUND: {len(errors)}")
    print("=" * 70)

    if errors:
        # Group by dataset
        datasets = {}
        for e in errors:
            ds = e["dataset"]
            if ds not in datasets:
                datasets[ds] = []
            datasets[ds].append(e)

        for ds, errs in datasets.items():
            print(f"\n{'='*50}")
            print(f"  {ds.upper()} — {len(errs)} errors")
            print(f"{'='*50}")
            for e in errs:
                print(f"\n  Row #{e['id']}:")
                print(f"    Problem: {e['problem'][:100]}")
                print(f"    Given answer: {e['expected_answer']}")
                print(f"    Issue: {e['issue']}")
    else:
        print("\nAll answers verified correctly!")
