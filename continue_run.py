#!/usr/bin/env python3
"""Continue an interrupted run, appending results to an existing results file."""

import json
import os
import sys

os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.storage import StorageManager
from src.question_processor import QuestionProcessor
from src.fairness_controller import FairnessController

# ---- CONFIG ----
RESULTS_FILE = "results/advanced_probability_statistics_problems_qwen3_4b_04-06-26T09-37-57.json"
DATASET_FILE = "advanced_probability_statistics_problems.xml"
MODEL = "qwen3:4b"
FAIRNESS_CONFIG = "config/fairness_config.json"
# ----------------

def main():
    # Load existing results to find already-processed IDs
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)
    processed_ids = {r["question_id"] for r in existing.get("results", [])}
    print(f"Already processed: {len(processed_ids)} questions")

    # Parse dataset
    parser = XMLParser(DATASET_FILE)
    cache_file = os.path.join("data", f"questions_{os.path.splitext(DATASET_FILE)[0]}.json")
    if os.path.exists(cache_file):
        questions = parser.load_questions_cache(cache_file)
    else:
        questions = parser.parse()
    print(f"Total questions in dataset: {len(questions)}")

    # Filter to only unprocessed questions
    remaining = [q for q in questions if q.id not in processed_ids]
    print(f"Remaining to process: {len(remaining)}")
    if not remaining:
        print("Nothing left to do!")
        return

    # Setup fairness controller
    fairness_controller = FairnessController(config_path=FAIRNESS_CONFIG)
    options_override = fairness_controller.build_ollama_options(MODEL)

    # Setup components
    ollama_client = OllamaClient(
        base_url="http://localhost:11434",
        model=MODEL,
        options_override=options_override,
    )
    storage_manager = StorageManager(data_dir="data", results_dir="results")

    # Point storage at the existing results file so saves append there
    storage_manager.results_file = RESULTS_FILE

    # Seed progress with already-processed IDs so processor skips them
    progress_data = {
        "last_processed_id": None,
        "processed_ids": list(processed_ids),
        "skipped_ids": [],
        "failed_ids": [],
        "session_start": existing["metadata"]["created"],
    }
    with open(storage_manager.progress_file, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=2, ensure_ascii=False)

    processor = QuestionProcessor(ollama_client, storage_manager, fairness_controller)

    # Run automatic processing on the full list (processor will skip already-done via progress)
    print(f"\nResuming from question {remaining[0].id}...")
    processor.process_questions_auto(questions)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Progress is saved — re-run to continue.")
        sys.exit(0)
