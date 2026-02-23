#!/usr/bin/env python3
"""Resume grade 8 math dataset from Q110 - one-time script."""

import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True, errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.storage import StorageManager
from src.question_processor import QuestionProcessor


def load_questions(xml_file):
    cache_name = os.path.splitext(os.path.basename(xml_file))[0]
    cache_path = os.path.join("data", f"questions_{cache_name}.json")
    parser = XMLParser(xml_file)
    if os.path.exists(cache_path):
        return parser.load_questions_cache(cache_path)
    else:
        questions = parser.parse()
        parser.save_questions_cache(cache_path)
        return questions


def seed_progress(existing_results_file, progress_file):
    """Seed progress.json with IDs from an existing results file."""
    with open(existing_results_file, encoding="utf-8") as f:
        data = json.load(f)
    processed_ids = [r["question_id"] for r in data["results"]]
    progress = {
        "processed_ids": processed_ids,
        "skipped_ids": [],
        "failed_ids": [],
        "last_processed_id": processed_ids[-1] if processed_ids else None,
        "last_updated": datetime.now().isoformat(),
        "session_start": datetime.now().isoformat(),
    }
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    return len(processed_ids)


def main():
    model = "gemma3:4b"
    client = OllamaClient(model=model)
    storage = StorageManager()
    processor = QuestionProcessor(client, storage)

    # --- Resume Grade 8 Math ---
    grade8_xml = "grade_8_math_problems.xml"
    grade8_existing = r"results\grade_8_math_problems_gemma3_4b_02-20-26T13-46-16.json"

    print("=" * 60)
    print(f"RESUMING: Grade 8 Math with {model}")
    print("=" * 60)

    # Seed progress with already-completed IDs
    count = seed_progress(grade8_existing, storage.progress_file)
    print(f"Seeded {count} already-processed question IDs")

    # Point to the existing results file WITHOUT resetting progress
    storage.results_file = grade8_existing
    print(f"Results file: {storage.results_file}")

    questions = load_questions(grade8_xml)
    print(f"Loaded {len(questions)} total questions, resuming from Q{count + 1}")
    processor.process_questions_auto(questions)

    print("\n" + "=" * 60)
    print("ALL DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
