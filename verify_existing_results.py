"""
Batch Verification Script
Verifies all existing results in data/results.json
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from verifier import verify_answer


def load_results(filepath='data/results.json'):
    """Load existing results from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Results file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in results file: {e}")
        return None


def save_results(data, filepath='data/results.json'):
    """Save updated results to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False


def main():
    print("=" * 70)
    print(" BATCH VERIFICATION OF EXISTING RESULTS")
    print("=" * 70)
    print()

    # Load existing results
    results_data = load_results()
    if results_data is None:
        return

    results = results_data.get("results", [])
    if not results:
        print("No results found to verify.")
        return

    print(f"Found {len(results)} existing results")
    print()

    # Track statistics
    stats = {
        "correct": 0,
        "incorrect": 0,
        "unable_to_verify": 0,
        "error": 0,
        "already_verified": 0,
        "newly_verified": 0
    }

    # Process each result
    for i, result in enumerate(results, 1):
        question_id = result.get("question_id", "unknown")

        # Skip if already verified
        if "verification" in result and result["verification"]:
            stats["already_verified"] += 1
            print(f"[{i}/{len(results)}] Question {question_id}: Already verified (skipping)")
            continue

        print(f"[{i}/{len(results)}] Verifying question {question_id}...", end=" ")

        # Get required fields
        llm_response = result.get("llm_response", "")
        expected_answer = result.get("expected_answer", "")
        alternate_answer = result.get("alternate_answer")

        # Verify
        verification = verify_answer(llm_response, expected_answer, alternate_answer)

        # Add verification to result
        result["verification"] = {
            "extracted_answer": verification.extracted_answer,
            "extraction_method": verification.extraction_method,
            "extraction_confidence": verification.extraction_confidence,
            "extracted_type": verification.extracted_normalized.answer_type.value if verification.extracted_normalized else None,
            "expected_type": verification.expected_normalized.answer_type.value,
            "is_correct": verification.is_correct,
            "comparison_confidence": verification.comparison_confidence,
            "match_type": verification.match_type,
            "matched_answer": verification.matched_answer,
            "verification_status": verification.verification_status
        }

        # Update stats
        stats[verification.verification_status] += 1
        stats["newly_verified"] += 1

        # Print status (use ASCII symbols for Windows compatibility)
        if verification.verification_status == "correct":
            print("[CORRECT]")
        elif verification.verification_status == "incorrect":
            print("[INCORRECT]")
        elif verification.verification_status == "unable_to_verify":
            print("[UNABLE TO VERIFY]")
        else:
            print("[ERROR]")

    # Save updated results
    print()
    print("Saving updated results...", end=" ")
    if save_results(results_data):
        print("[Done]")
    else:
        print("[Failed]")
        return

    # Print summary
    print()
    print("=" * 70)
    print(" VERIFICATION SUMMARY")
    print("=" * 70)

    total_verified = stats["correct"] + stats["incorrect"]
    if total_verified > 0:
        accuracy = (stats["correct"] / total_verified) * 100
        print(f"\nAccuracy: {stats['correct']}/{total_verified} ({accuracy:.1f}%)")

    print(f"\nBreakdown:")
    print(f"  Correct:            {stats['correct']}")
    print(f"  Incorrect:          {stats['incorrect']}")
    print(f"  Unable to verify:   {stats['unable_to_verify']}")
    print(f"  Errors:             {stats['error']}")
    print(f"  Already verified:   {stats['already_verified']}")
    print(f"  Newly verified:     {stats['newly_verified']}")
    print(f"  Total:              {len(results)}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
