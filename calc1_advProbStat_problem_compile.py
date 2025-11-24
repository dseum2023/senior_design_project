#!/usr/bin/env python3
# Requires: pip install datasets

import re
import random
from typing import Dict, Any, Iterable, List
from xml.etree.ElementTree import Element, SubElement, ElementTree

from datasets import load_dataset

# ---------------
# XML helpers
# ---------------

def _indent_xml(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            _indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def write_xml(rows: List[Dict[str, str]], xml_path: str):
    """Write problems in the format matching grade_8_math_problems.xml"""
    root = Element("rows")
    for idx, r in enumerate(rows, start=1):
        row = SubElement(root, "row", {"id": str(idx)})
        SubElement(row, "ProblemNumber").text = str(r.get("ProblemNumber", idx))
        SubElement(row, "Directions").text = r.get("Directions", "")
        SubElement(row, "Problem").text = r.get("Problem", "")
        SubElement(row, "Solution").text = r.get("Solution", "")
        SubElement(row, "AlternateSolution").text = r.get("AlternateSolution", "")
        SubElement(row, "CommonCoreCategory").text = r.get("CommonCoreCategory", "")
    _indent_xml(root)
    ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True, short_empty_elements=False)

# ------------------------------
# Synthetic Problem Generators
# ------------------------------

def generate_limit_problems() -> List[Dict[str, Any]]:
    """Generate limit problems"""
    problems = []
    
    # Basic polynomial limits
    for _ in range(80):
        x_val = random.randint(-10, 10)
        a = random.randint(1, 5)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        result = a * x_val**2 + b * x_val + c
        problems.append({
            "problem": f"lim(x->{x_val}) [{a}x^2 + {b}x + {c}]",
            "solution": str(result),
            "directions": "Evaluate the limit."
        })
    
    # Limits at infinity
    for _ in range(40):
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        if random.choice([True, False]):
            problems.append({
                "problem": f"lim(x->infinity) [{a}x^3 / {b}x^3]",
                "solution": str(round(a/b, 2)),
                "directions": "Evaluate the limit."
            })
        else:
            problems.append({
                "problem": f"lim(x->infinity) [{a}x^2 / {b}x^3]",
                "solution": "0",
                "directions": "Evaluate the limit."
            })
    
    # Limits with factoring
    for _ in range(30):
        a = random.randint(1, 5)
        problems.append({
            "problem": f"lim(x->{a}) [(x^2 - {a**2}) / (x - {a})]",
            "solution": str(2 * a),
            "directions": "Evaluate the limit by factoring."
        })
    
    return problems

def generate_derivative_problems() -> List[Dict[str, Any]]:
    """Generate derivative problems"""
    problems = []
    
    # Power rule
    for _ in range(100):
        n = random.randint(2, 10)
        coef = random.randint(1, 10)
        problems.append({
            "problem": f"f(x) = {coef}x^{n}",
            "solution": f"f'(x) = {coef * n}x^{n-1}",
            "directions": "Find the derivative using the power rule."
        })
    
    # Sum rule
    for _ in range(80):
        n1 = random.randint(2, 5)
        n2 = random.randint(2, 5)
        c1 = random.randint(1, 8)
        c2 = random.randint(1, 8)
        const = random.randint(-10, 10)
        problems.append({
            "problem": f"f(x) = {c1}x^{n1} + {c2}x^{n2} + {const}",
            "solution": f"f'(x) = {c1*n1}x^{n1-1} + {c2*n2}x^{n2-1}",
            "directions": "Find the derivative."
        })
    
    # Product rule
    for _ in range(60):
        a = random.randint(2, 5)
        b = random.randint(2, 5)
        problems.append({
            "problem": f"f(x) = x^{a} · sin(x)",
            "solution": f"f'(x) = {a}x^{a-1}·sin(x) + x^{a}·cos(x)",
            "directions": "Find the derivative using the product rule."
        })
    
    # Quotient rule
    for _ in range(40):
        a = random.randint(1, 5)
        b = random.randint(1, 5)
        problems.append({
            "problem": f"f(x) = x^{a} / x^{b}",
            "solution": f"f'(x) = {a-b}x^{a-b-1}" if a != b else "f'(x) = 0",
            "directions": "Find the derivative using the quotient rule."
        })
    
    # Chain rule
    for _ in range(70):
        n = random.randint(2, 6)
        inner_coef = random.randint(2, 5)
        const = random.randint(-5, 5)
        problems.append({
            "problem": f"f(x) = ({inner_coef}x + {const})^{n}",
            "solution": f"f'(x) = {n}({inner_coef}x + {const})^{n-1} · {inner_coef}",
            "directions": "Find the derivative using the chain rule."
        })
    
    return problems

def generate_integral_problems() -> List[Dict[str, Any]]:
    """Generate integration problems"""
    problems = []
    
    # Indefinite integrals - power rule
    for _ in range(100):
        n = random.randint(1, 8)
        coef = random.randint(1, 10)
        if n == -1:
            n = random.randint(2, 8)
        problems.append({
            "problem": f"integral of {coef}x^{n} dx",
            "solution": f"({coef}/{n+1})x^{n+1} + C",
            "directions": "Find the indefinite integral."
        })
    
    # Definite integrals
    for _ in range(100):
        a = random.randint(0, 3)
        b = random.randint(a+1, 8)
        n = random.randint(1, 4)
        coef = random.randint(1, 5)
        upper = coef * (b**(n+1)) / (n+1)
        lower = coef * (a**(n+1)) / (n+1)
        result = round(upper - lower, 2)
        problems.append({
            "problem": f"integral from {a} to {b} of {coef}x^{n} dx",
            "solution": str(result),
            "directions": "Evaluate the definite integral."
        })
    
    # Trigonometric integrals
    for _ in range(50):
        coef = random.randint(1, 5)
        trig_func = random.choice(["sin(x)", "cos(x)"])
        if trig_func == "sin(x)":
            problems.append({
                "problem": f"integral of {coef}sin(x) dx",
                "solution": f"-{coef}cos(x) + C",
                "directions": "Find the indefinite integral."
            })
        else:
            problems.append({
                "problem": f"integral of {coef}cos(x) dx",
                "solution": f"{coef}sin(x) + C",
                "directions": "Find the indefinite integral."
            })
    
    return problems

def generate_application_problems() -> List[Dict[str, Any]]:
    """Generate application problems"""
    problems = []
    
    # Critical points / optimization
    for _ in range(70):
        a = random.randint(1, 5)
        b = random.randint(-10, 10)
        c = random.randint(-10, 10)
        x_crit = round(-b / (2 * a), 2)
        problems.append({
            "problem": f"Find the critical points of f(x) = {a}x^2 + {b}x + {c}",
            "solution": f"x = {x_crit}",
            "directions": "Find all critical points by setting f'(x) = 0."
        })
    
    # Related rates
    for _ in range(40):
        rate = random.randint(2, 10)
        radius = random.randint(2, 6)
        result = round(2 * 3.14159 * radius * rate, 2)
        problems.append({
            "problem": f"The radius of a circle is increasing at {rate} cm/s. Find the rate of change of the area when r = {radius} cm. Use pi = 3.14159.",
            "solution": f"{result}",
            "directions": "Use related rates to solve. Round to 2 decimal places."
        })
    
    # Tangent lines
    for _ in range(40):
        a = random.randint(1, 5)
        x0 = random.randint(-5, 5)
        y0 = a * x0**2
        slope = 2 * a * x0
        b_intercept = y0 - slope * x0
        problems.append({
            "problem": f"Find the slope of the tangent line to f(x) = {a}x^2 at x = {x0}",
            "solution": f"{slope}",
            "directions": "Find the slope of the tangent line."
        })
    
    return problems

def generate_probability_problems() -> List[Dict[str, Any]]:
    """Generate probability and statistics problems"""
    problems = []
    
    # Expected value
    for _ in range(150):
        n = random.randint(3, 6)
        outcomes = [random.randint(1, 100) for _ in range(n)]
        probs = [round(random.random(), 2) for _ in range(n-1)]
        probs.append(round(1 - sum(probs), 2))
        if abs(sum(probs) - 1.0) > 0.01:
            probs[-1] = round(1 - sum(probs[:-1]), 2)
        
        exp_val = sum(o * p for o, p in zip(outcomes, probs))
        prob_str = ", ".join([f"P(X={o}) = {p}" for o, p in zip(outcomes, probs)])
        problems.append({
            "problem": f"A random variable X has the following distribution: {prob_str}. Find E(X). Round to 2 decimal places.",
            "solution": f"{round(exp_val, 2)}",
            "directions": "Compute the expected value."
        })
    
    # Variance
    for _ in range(100):
        outcomes = [random.randint(1, 20) for _ in range(3)]
        probs = [0.3, 0.5, 0.2]
        exp_val = sum(o * p for o, p in zip(outcomes, probs))
        variance = sum(p * (o - exp_val)**2 for o, p in zip(outcomes, probs))
        prob_str = ", ".join([f"P(X={o}) = {p}" for o, p in zip(outcomes, probs)])
        problems.append({
            "problem": f"X has distribution: {prob_str}. Find Var(X). Round to 2 decimal places.",
            "solution": f"{round(variance, 2)}",
            "directions": "Compute the variance."
        })
    
    # Binomial distribution - just calculate binomial coefficient
    for _ in range(150):
        n = random.randint(5, 12)
        k = random.randint(0, n)
        # Calculate binomial coefficient
        from math import factorial
        binom_coef = factorial(n) // (factorial(k) * factorial(n - k))
        problems.append({
            "problem": f"Calculate the binomial coefficient C({n},{k}).",
            "solution": f"{binom_coef}",
            "directions": "Calculate using the combination formula."
        })
    
    # Normal distribution - z-scores
    for _ in range(150):
        mu = random.randint(-10, 10)
        sigma = random.randint(1, 5)
        x = random.randint(mu-10, mu+10)
        z = (x - mu) / sigma
        problems.append({
            "problem": f"For X ~ N(mean={mu}, std_dev={sigma}), find the z-score when X = {x}. Round to 2 decimal places.",
            "solution": f"{round(z, 2)}",
            "directions": "Calculate the z-score using z = (x - mean) / std_dev."
        })
    
    # Conditional probability
    for _ in range(150):
        pa = round(random.uniform(0.3, 0.7), 2)
        pb_given_a = round(random.uniform(0.3, 0.8), 2)
        p_a_and_b = round(pa * pb_given_a, 3)
        problems.append({
            "problem": f"If P(A) = {pa} and P(B|A) = {pb_given_a}, find P(A and B). Round to 3 decimal places.",
            "solution": f"{p_a_and_b}",
            "directions": "Use the formula P(A and B) = P(A) * P(B|A)."
        })
    
    # Combinations
    for _ in range(150):
        n = random.randint(5, 12)
        r = random.randint(2, min(n, 6))
        from math import factorial
        result = factorial(n) // (factorial(r) * factorial(n - r))
        problems.append({
            "problem": f"How many ways can you choose {r} items from {n} distinct items?",
            "solution": f"{result}",
            "directions": "Calculate the number of combinations C({n},{r})."
        })
    
    # Permutations
    for _ in range(100):
        n = random.randint(5, 10)
        r = random.randint(2, min(n, 5))
        from math import factorial
        result = factorial(n) // factorial(n - r)
        problems.append({
            "problem": f"How many ways can you arrange {r} items from {n} distinct items?",
            "solution": f"{result}",
            "directions": "Calculate the number of permutations P({n},{r})."
        })
    
    # Simple probability
    for _ in range(50):
        total = random.randint(10, 30)
        favorable = random.randint(1, total-1)
        prob = round(favorable / total, 3)
        problems.append({
            "problem": f"A bag contains {total} balls, {favorable} of which are red. What is the probability of selecting a red ball? Round to 3 decimal places.",
            "solution": f"{prob}",
            "directions": "Calculate probability as favorable outcomes / total outcomes."
        })
    
    return problems

# ------------------------------
# Main pipeline
# ------------------------------

def main():
    print("Generating Calculus I problems...")
    calc_problems = []
    calc_problems.extend(generate_limit_problems())
    calc_problems.extend(generate_derivative_problems())
    calc_problems.extend(generate_integral_problems())
    calc_problems.extend(generate_application_problems())
    
    # Shuffle and create rows
    random.shuffle(calc_problems)
    calc_rows = []
    for i, prob in enumerate(calc_problems[:1000], 1):
        calc_rows.append({
            "ProblemNumber": str(i),
            "Directions": prob["directions"],
            "Problem": prob["problem"],
            "Solution": prob["solution"],
            "AlternateSolution": "",
            "CommonCoreCategory": "Calculus I"
        })
    
    print("Generating Advanced Probability & Statistics problems...")
    prob_problems = generate_probability_problems()
    random.shuffle(prob_problems)
    
    prob_rows = []
    for i, prob in enumerate(prob_problems[:1000], 1):
        prob_rows.append({
            "ProblemNumber": str(i),
            "Directions": prob["directions"],
            "Problem": prob["problem"],
            "Solution": prob["solution"],
            "AlternateSolution": "",
            "CommonCoreCategory": "Advanced Probability & Statistics"
        })
    
    # Write XMLs
    write_xml(calc_rows, "calculus1_problems.xml")
    write_xml(prob_rows, "advanced_probability_statistics_problems.xml")
    
    print(f"\nWrote {len(calc_rows)} Calculus I problems to calculus1_problems.xml")
    print(f"Wrote {len(prob_rows)} Advanced Probability & Statistics problems to advanced_probability_statistics_problems.xml")

if __name__ == "__main__":
    main()