"""
Re-verification Script
Sweeps all result files and re-runs verification with the updated pipeline,
then writes back corrected is_correct flags and summary statistics.
"""

import json
import os
import sys

# Make src importable from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from verifier import verify_answer


def _verification_to_dict(vr) -> dict:
    """Convert a VerificationResult to the dict format stored in result files."""
    extracted_type = None
    expected_type = None
    if vr.extracted_normalized is not None:
        extracted_type = vr.extracted_normalized.answer_type.value
    if vr.expected_normalized is not None:
        expected_type = vr.expected_normalized.answer_type.value

    return {
        "extracted_answer": vr.extracted_answer,
        "extraction_method": vr.extraction_method,
        "extraction_confidence": vr.extraction_confidence,
        "extracted_type": extracted_type,
        "expected_type": expected_type,
        "is_correct": vr.is_correct,
        "comparison_confidence": vr.comparison_confidence,
        "match_type": vr.match_type,
        "matched_answer": vr.matched_answer,
        "verification_status": vr.verification_status,
    }


def _compute_summary(results: list) -> dict:
    count = len(results)
    total_time = sum(float(r.get("processing_time") or 0.0) for r in results)
    avg_time = (total_time / count) if count > 0 else 0.0
    correct = sum(1 for r in results if r.get("is_correct") is True)
    pct = (correct / count * 100.0) if count > 0 else 0.0
    return {
        "total_time_seconds": total_time,
        "average_time_per_question_seconds": avg_time,
        "questions_answered": count,
        "questions_correct": correct,
        "percent_correct": pct,
    }


def reverify_file(filepath: str) -> dict:
    """Re-verify a single result file. Returns change statistics."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    old_correct = sum(1 for r in results if r.get("is_correct") is True)

    changed = 0
    newly_correct = 0
    newly_incorrect = 0

    for r in results:
        llm_response = r.get("llm_response") or ""
        expected = r.get("expected_answer") or ""
        alternate = r.get("alternate_answer") or None

        if not llm_response.strip() or not expected.strip():
            # No response or no expected answer — skip (keep as-is)
            continue

        vr = verify_answer(llm_response, expected, alternate)
        new_verification = _verification_to_dict(vr)
        old_correct_flag = r.get("is_correct")

        r["verification"] = new_verification
        r["is_correct"] = vr.is_correct

        if old_correct_flag != vr.is_correct:
            changed += 1
            if vr.is_correct:
                newly_correct += 1
            else:
                newly_incorrect += 1

    new_correct = sum(1 for r in results if r.get("is_correct") is True)
    data["summary"] = _compute_summary(results)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        "file": filepath,
        "total": len(results),
        "old_correct": old_correct,
        "new_correct": new_correct,
        "changed": changed,
        "newly_correct": newly_correct,
        "newly_incorrect": newly_incorrect,
    }


def find_result_files(results_dir: str) -> list:
    """Recursively find all result JSON files (excluding the top-level results.json summary)."""
    found = []
    for root, dirs, files in os.walk(results_dir):
        for fname in files:
            if fname.endswith(".json") and fname != "results.json":
                found.append(os.path.join(root, fname))
    return sorted(found)


def main():
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    files = find_result_files(results_dir)

    if not files:
        print("No result files found.")
        return

    print(f"Re-verifying {len(files)} result file(s)...\n")
    total_changed = 0
    total_newly_correct = 0
    total_newly_incorrect = 0

    for fpath in files:
        try:
            stats = reverify_file(fpath)
        except json.JSONDecodeError as e:
            print(f"  SKIPPED (corrupt JSON): {os.path.relpath(fpath, results_dir)} — {e}")
            continue
        name = os.path.relpath(fpath, results_dir)
        delta = stats["new_correct"] - stats["old_correct"]
        sign = "+" if delta >= 0 else ""
        print(
            f"  {name}: {stats['old_correct']} -> {stats['new_correct']} correct "
            f"({sign}{delta})  |  {stats['changed']} result(s) changed "
            f"(+{stats['newly_correct']} correct, -{stats['newly_incorrect']} incorrect)"
        )
        total_changed += stats["changed"]
        total_newly_correct += stats["newly_correct"]
        total_newly_incorrect += stats["newly_incorrect"]

    print(f"\nDone. Total changes: {total_changed} "
          f"(+{total_newly_correct} newly correct, -{total_newly_incorrect} newly incorrect)")


if __name__ == "__main__":
    main()
