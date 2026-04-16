#!/usr/bin/env python3
"""
Resume script: finish gemma3:4b on advanced_probability_statistics_problems.
Appends remaining answers to the existing in-progress results file.
"""

import json
import os
import sys
import time

# Make src importable
sys.path.insert(0, os.path.dirname(__file__))

from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.verifier import verify_answer
from src.resource_monitor import ResourceMonitor

RESULTS_FILE = os.path.join(
    os.path.dirname(__file__),
    "results",
    "advanced_probability_statistics_problems_gemma3_4b_04-03-26T09-56-19.json",
)
XML_FILE = os.path.join(
    os.path.dirname(__file__),
    "advanced_probability_statistics_problems.xml",
)
MODEL = "gemma3:4b"

OLLAMA_OPTIONS = {
    "num_ctx": 4096,
    "num_gpu": 999,
    "num_thread": 8,
    "num_predict": 16384,
    "temperature": 0.3,
    "top_p": 0.9,
    "top_k": 40,
}


def load_results(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compute_summary(results: list) -> dict:
    n = len(results)
    total_time = sum(float(r.get("processing_time", 0) or 0) for r in results)
    correct = sum(1 for r in results if r.get("is_correct") is True)
    pct = (correct / n * 100) if n else 0.0

    summary = {
        "total_time_seconds": total_time,
        "average_time_per_question_seconds": total_time / n if n else 0.0,
        "questions_answered": n,
        "questions_correct": correct,
        "percent_correct": pct,
    }

    sys_results = [r for r in results if r.get("system_metrics")]
    if sys_results:
        sn = len(sys_results)
        summary["resource_metrics_avg"] = {
            "gpu_power_avg_w": round(sum(r["system_metrics"]["gpu_power_avg_w"] for r in sys_results) / sn, 1),
            "gpu_vram_peak_mb": round(max(r["system_metrics"]["gpu_vram_peak_mb"] for r in sys_results), 1),
            "cpu_avg_percent": round(sum(r["system_metrics"]["cpu_avg_percent"] for r in sys_results) / sn, 1),
            "ram_peak_mb": round(max(r["system_metrics"]["ram_peak_mb"] for r in sys_results), 1),
            "total_energy_wh": round(sum(r["system_metrics"]["energy_estimate_wh"] for r in sys_results), 4),
        }

    om_results = [r for r in results if r.get("ollama_metrics")]
    if om_results:
        total_gen = sum(r["ollama_metrics"].get("eval_count", 0) for r in om_results)
        total_prompt = sum(r["ollama_metrics"].get("prompt_eval_count", 0) for r in om_results)
        gen_speeds = [r["ollama_metrics"]["generation_speed_tps"] for r in om_results if r["ollama_metrics"].get("generation_speed_tps", 0) > 0]
        prompt_speeds = [r["ollama_metrics"]["prompt_processing_speed_tps"] for r in om_results if r["ollama_metrics"].get("prompt_processing_speed_tps", 0) > 0]
        ratios = [r["ollama_metrics"]["output_to_input_ratio"] for r in om_results if r["ollama_metrics"].get("output_to_input_ratio", 0) > 0]
        overheads = [r["ollama_metrics"].get("ollama_overhead_s", 0) for r in om_results]
        summary["ollama_metrics_avg"] = {
            "total_generated_tokens": total_gen,
            "total_prompt_tokens": total_prompt,
            "avg_generation_speed_tps": round(sum(gen_speeds) / len(gen_speeds), 2) if gen_speeds else 0.0,
            "avg_prompt_processing_speed_tps": round(sum(prompt_speeds) / len(prompt_speeds), 2) if prompt_speeds else 0.0,
            "avg_output_to_input_ratio": round(sum(ratios) / len(ratios), 2) if ratios else 0.0,
            "avg_ollama_overhead_s": round(sum(overheads) / len(overheads), 4) if overheads else 0.0,
        }

    return summary


def main():
    print(f"Loading existing results from:\n  {RESULTS_FILE}")
    data = load_results(RESULTS_FILE)
    existing_ids = {str(r["question_id"]) for r in data["results"]}
    print(f"Already answered: {len(existing_ids)} questions")

    print(f"\nParsing XML: {XML_FILE}")
    parser = XMLParser(XML_FILE)
    all_questions = parser.parse()

    remaining = [q for q in all_questions if str(q.id) not in existing_ids]
    print(f"Remaining: {len(remaining)} questions (IDs {remaining[0].id}–{remaining[-1].id})")

    client = OllamaClient(model=MODEL, options_override=OLLAMA_OPTIONS)
    if not client.test_connection():
        print("ERROR: Cannot connect to Ollama. Is it running?")
        sys.exit(1)
    if not client.check_model_availability():
        print(f"ERROR: Model {MODEL} not available in Ollama.")
        sys.exit(1)
    print(f"Connected to Ollama, model {MODEL} ready.\n")

    resource_monitor = ResourceMonitor(sample_interval=0.5)

    for i, question in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] Q#{question.id}: {question.question_text[:70]}...")

        with resource_monitor:
            response = client.query_llm(question.question_text)
        metrics = resource_monitor.get_metrics()

        verification_dict = None
        is_correct = None

        if response.success:
            verification = verify_answer(
                llm_response=response.response_text,
                expected_answer=question.answer,
                alternate_answer=question.alternate_answer,
            )
            is_correct = verification.is_correct
            verification_dict = {
                "extracted_answer": verification.extracted_answer,
                "extraction_method": verification.extraction_method,
                "extraction_confidence": verification.extraction_confidence,
                "extracted_type": verification.extracted_normalized.answer_type.value if verification.extracted_normalized else None,
                "expected_type": verification.expected_normalized.answer_type.value,
                "is_correct": verification.is_correct,
                "comparison_confidence": verification.comparison_confidence,
                "match_type": verification.match_type,
                "matched_answer": verification.matched_answer,
                "verification_status": verification.verification_status,
            }
            status = "CORRECT" if is_correct else ("INCORRECT" if is_correct is False else "UNVERIFIED")
            print(f"  -> {status} | {response.processing_time:.2f}s | extracted: {verification.extracted_answer}")
        else:
            print(f"  -> FAILED: {response.error_message}")

        result = {
            "question_id": str(question.id),
            "category": question.category,
            "question_text": question.question_text,
            "expected_answer": question.answer,
            "llm_response": response.response_text,
            "processing_time": response.processing_time,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "success": response.success,
            "error_message": response.error_message,
            "model_used": response.model_used or MODEL,
            "alternate_answer": question.alternate_answer,
            "verification": verification_dict,
            "is_correct": is_correct,
            "system_metrics": metrics.to_dict() if metrics else None,
            "ollama_metrics": response.ollama_metrics,
            "fairness_metadata": data["results"][0].get("fairness_metadata") if data["results"] else None,
        }

        # Append and persist after every question
        data["results"].append(result)
        data["metadata"]["processed_questions"] = len(data["results"])
        data["metadata"]["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        if response.success:
            data["metadata"]["successful_responses"] = data["metadata"].get("successful_responses", 0) + 1
        else:
            data["metadata"]["failed_responses"] = data["metadata"].get("failed_responses", 0) + 1
        data["summary"] = compute_summary(data["results"])
        save_results(RESULTS_FILE, data)

    total = len(data["results"])
    correct = data["summary"]["questions_correct"]
    pct = data["summary"]["percent_correct"]
    print(f"\nDone! {total} total questions | {correct} correct ({pct:.2f}%)")
    print(f"Results saved to:\n  {RESULTS_FILE}")


if __name__ == "__main__":
    main()
