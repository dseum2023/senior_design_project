#!/usr/bin/env python3
"""
Math LLM Tester - Main Application
Interactive tool for testing math questions with local LLM via Ollama
"""

import argparse
import os
import sys
from typing import Dict, List, Optional

# Force unbuffered output for real-time streaming
os.environ["PYTHONUNBUFFERED"] = "1"

# Configure stdout for immediate flushing
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True, errors="replace")

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.storage import StorageManager
from src.question_processor import QuestionProcessor


MODEL_OPTIONS = {
    "1": "gpt-oss:20b",
    "2": "qwen3:8b",
    "3": "gemma3:12b",
}

DATASET_OPTIONS = {
    "1": {
        "file": "calculus1_problems.xml",
        "name": "Calculus 1",
        "description": "Comprehensive calculus problems",
    },
    "2": {
        "file": "advanced_probability_statistics_problems.xml",
        "name": "Probability & Statistics",
        "description": "Advanced probability and statistics problems",
    },
    "3": {
        "file": "grade_8_math_problems.xml",
        "name": "Grade 8 Math",
        "description": "Grade 8 mathematics problems",
    },
}


def print_banner() -> None:
    """Print application banner"""
    print("=" * 60)
    print("🧮 MATH LLM TESTER")
    print("=" * 60)
    print("Interactive tool for testing math questions with LLM")
    print(f"Models: {', '.join(MODEL_OPTIONS.values())} via Ollama")
    print("=" * 60)


def get_available_datasets() -> Dict[str, Dict[str, str]]:
    """Get list of available dataset XML files"""
    available = {}
    for key, dataset in DATASET_OPTIONS.items():
        if os.path.exists(dataset["file"]):
            available[key] = dataset
    return available


def select_model() -> str:
    """Prompt user to select a model"""
    default_key = "1"
    default_model = MODEL_OPTIONS[default_key]

    print("\n" + "=" * 60)
    print("🤖 MODEL SELECTION")
    print("=" * 60)

    for key, model in MODEL_OPTIONS.items():
        print(f"{key}. {model}")

    print(f"\nPress Enter to use default: {default_model}")

    while True:
        choice = input(f"Select model (1-{len(MODEL_OPTIONS)}): ").strip()

        if choice == "":
            print(f"✅ Selected model: {default_model}")
            return default_model

        if choice in MODEL_OPTIONS:
            selected_model = MODEL_OPTIONS[choice]
            print(f"✅ Selected model: {selected_model}")
            return selected_model

        print(f"Invalid choice. Please enter a number between 1 and {len(MODEL_OPTIONS)}.")


def _print_dataset_selection(selected_datasets: List[Dict[str, str]]) -> None:
    selected_names = ", ".join(dataset["name"] for dataset in selected_datasets)
    print(f"\n✅ Selected: {selected_names}")


def select_datasets(datasets: Dict[str, Dict[str, str]]) -> Optional[List[Dict[str, str]]]:
    """Prompt user to select one or more datasets"""
    print("\n" + "=" * 60)
    print("📚 DATASET SELECTION")
    print("=" * 60)

    if not datasets:
        print("❌ No dataset XML files found!")
        print("Please ensure at least one of these files exists:")
        print("  - calculus1_problems.xml")
        print("  - advanced_probability_statistics_problems.xml")
        print("  - grade_8_math_problems.xml")
        return None

    print("\nAvailable datasets:")
    for key in sorted(datasets.keys(), key=int):
        dataset = datasets[key]
        print(f"{key}. {dataset['name']}")
        print(f"   {dataset['description']}")
        print(f"   File: {dataset['file']}")
        print()

    print("A. All available datasets")

    available_keys = sorted(datasets.keys(), key=int)
    prompt_range = f"{available_keys[0]}-{available_keys[-1]}"

    while True:
        choice = input(f"Select dataset(s) {prompt_range} separated by commas, or A for all: ").strip()

        if not choice:
            print("Invalid choice. Please enter one or more dataset numbers, or A.")
            continue

        if choice.upper() == "A":
            selected = [datasets[key] for key in available_keys]
            _print_dataset_selection(selected)
            return selected

        requested_keys = [key.strip() for key in choice.split(",") if key.strip()]
        invalid_keys = [key for key in requested_keys if key not in datasets]

        if invalid_keys:
            print(f"Invalid dataset selection: {', '.join(invalid_keys)}")
            print("Please enter valid dataset numbers from the list, or A for all.")
            continue

        selected = []
        seen = set()
        for key in requested_keys:
            if key not in seen:
                selected.append(datasets[key])
                seen.add(key)

        if selected:
            _print_dataset_selection(selected)
            return selected


def resolve_dataset_argument(
    dataset_arg: str, datasets: Dict[str, Dict[str, str]]
) -> Optional[List[Dict[str, str]]]:
    """Resolve --dataset argument into selected dataset definitions"""
    tokens = [token.strip() for token in dataset_arg.split(",") if token.strip()]
    if not tokens:
        return None

    available_keys = sorted(datasets.keys(), key=int)

    if len(tokens) == 1 and tokens[0].upper() == "A":
        return [datasets[key] for key in available_keys]

    selected = []
    seen_files = set()

    for token in tokens:
        if token in datasets:
            dataset = datasets[token]
        elif token.isdigit():
            print(f"❌ Dataset option '{token}' is not available.")
            return None
        else:
            xml_file = token
            dataset_name = os.path.splitext(os.path.basename(xml_file))[0] or xml_file
            dataset = {
                "file": xml_file,
                "name": dataset_name,
                "description": "Custom dataset",
            }

        if dataset["file"] not in seen_files:
            selected.append(dataset)
            seen_files.add(dataset["file"])

    return selected if selected else None


def check_prerequisites(dataset_files: List[str]) -> bool:
    """Check if all prerequisites are met"""
    print("\n🔍 Checking prerequisites...")

    for xml_file in dataset_files:
        if not os.path.exists(xml_file):
            print(f"❌ XML file not found: {xml_file}")
            print("Please ensure the dataset XML file is in the current directory.")
            return False
        print(f"✅ Found XML file: {xml_file}")

    return True


def setup_components(ollama_url: str, model_name: str) -> Optional[tuple]:
    """
    Set up all application components

    Args:
        ollama_url: URL for Ollama server
        model_name: Name of the LLM model to use

    Returns:
        Tuple of (ollama_client, storage_manager, processor) or None if setup fails
    """
    try:
        print(f"🤖 Initializing Ollama client (URL: {ollama_url}, Model: {model_name})...")
        ollama_client = OllamaClient(base_url=ollama_url, model=model_name)

        print("💾 Initializing storage manager...")
        storage_manager = StorageManager()

        print("⚙️  Initializing question processor...")
        processor = QuestionProcessor(ollama_client, storage_manager)

        return ollama_client, storage_manager, processor

    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return None


def get_cache_file_path(xml_file: str) -> str:
    """Build a dataset-specific cache file path"""
    dataset_name = os.path.splitext(os.path.basename(xml_file))[0]
    safe_dataset_name = "".join(
        ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in dataset_name
    )
    return os.path.join("data", f"questions_{safe_dataset_name}.json")


def load_questions(xml_file: str) -> Optional[list]:
    """Load questions from XML file or dataset-specific cache"""
    print(f"\n📖 Preparing dataset: {xml_file}")

    parser = XMLParser(xml_file)
    cache_file = get_cache_file_path(xml_file)

    try:
        if os.path.exists(cache_file):
            print("📂 Loading questions from cache...")
            questions = parser.load_questions_cache(cache_file)
        else:
            print("📖 Parsing XML file...")
            questions = parser.parse()
            print("💾 Saving questions cache...")
            parser.save_questions_cache(cache_file)

        print(f"✅ Loaded {len(questions)} questions")

        metadata = parser.get_metadata()
        if metadata:
            print(f"📊 Dataset: {metadata.get('name', 'Unknown')}")
            print(f"📝 Description: {metadata.get('description', 'N/A')}")
            print(f"🏷️  Topics: {metadata.get('topics', 'N/A')}")

            categories = metadata.get("categories", {})
            if categories:
                print(f"📂 Categories: {len(categories)} categories")
                sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                for cat, count in sorted_cats:
                    print(f"   • {cat}: {count} questions")

        return questions

    except Exception as e:
        print(f"❌ Error loading questions: {e}")
        return None


def select_processing_mode() -> str:
    """Prompt user to choose processing mode"""
    print("\n" + "=" * 50)
    print("⚙️ PROCESSING MODE")
    print("=" * 50)
    print("1. Question-by-question (interactive)")
    print("2. Automatic sequential (run all remaining)")

    while True:
        choice = input("Select processing mode (1-2): ").strip()
        if choice == "1":
            return "interactive"
        if choice == "2":
            return "automatic"
        print("Invalid choice. Please enter 1 or 2.")


def show_menu() -> str:
    """Show main menu and get user choice"""
    print("\n" + "=" * 50)
    print("📋 MAIN MENU")
    print("=" * 50)
    print("1. Start processing questions")
    print("2. Show progress summary")
    print("3. Export results to CSV")
    print("4. Test Ollama connection")
    print("5. Show question statistics")
    print("6. Exit")
    print("=" * 50)

    while True:
        choice = input("Select option (1-6): ").strip()
        if choice in ["1", "2", "3", "4", "5", "6"]:
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")


def test_ollama_connection(ollama_client: OllamaClient) -> None:
    """Test Ollama connection and model availability"""
    print("\n🔧 Testing Ollama Connection...")
    print("-" * 40)

    if ollama_client.test_connection():
        print("✅ Ollama server is running")
    else:
        print("❌ Cannot connect to Ollama server")
        print(f"   URL: {ollama_client.base_url}")
        print("   Please ensure Ollama is running and accessible.")
        return

    if ollama_client.check_model_availability():
        print(f"✅ Model '{ollama_client.model}' is available")
    else:
        print(f"❌ Model '{ollama_client.model}' is not available")
        print(f"   Please install the model using: ollama pull {ollama_client.model}")
        return

    print("\n🧪 Testing with sample question...")
    test_question = "What is the derivative of x^2?"

    response = ollama_client.query_llm(test_question)

    if response.success:
        print(f"✅ Test successful! ({response.processing_time:.2f}s)")
        print(f"Response: {response.response_text[:100]}...")
    else:
        print(f"❌ Test failed: {response.error_message}")


def show_question_statistics(questions: list) -> None:
    """Show statistics about the questions"""
    print("\n📊 Question Statistics")
    print("-" * 40)

    if not questions:
        print("No questions loaded.")
        return

    categories = {}
    for question in questions:
        cat = question.category
        categories[cat] = categories.get(cat, 0) + 1

    print(f"Total Questions: {len(questions)}")
    print(f"Categories: {len(categories)}")
    print("\nQuestions by Category:")

    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    for category, count in sorted_cats:
        percentage = (count / len(questions)) * 100
        print(f"  {category:25} {count:4d} ({percentage:5.1f}%)")


def get_dataset_questions(
    xml_file: str, loaded_datasets: Dict[str, list]
) -> Optional[list]:
    """Load and memoize dataset questions"""
    if xml_file in loaded_datasets:
        return loaded_datasets[xml_file]

    questions = load_questions(xml_file)
    if questions is None:
        return None

    loaded_datasets[xml_file] = questions
    return questions


def process_selected_datasets(
    selected_datasets: List[Dict[str, str]],
    loaded_datasets: Dict[str, list],
    processor: QuestionProcessor,
    processing_mode: str,
) -> bool:
    """Process all selected datasets in the chosen mode"""
    for dataset in selected_datasets:
        xml_file = dataset["file"]
        questions = get_dataset_questions(xml_file, loaded_datasets)
        if questions is None:
            return False

        if processing_mode == "automatic":
            processor.process_questions_auto(questions)
        else:
            processor.process_questions(questions)

    return True


def main() -> None:
    """Main application entry point"""
    arg_parser = argparse.ArgumentParser(description="Math LLM Tester")
    arg_parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434)",
    )
    arg_parser.add_argument(
        "--model",
        default=None,
        help="LLM model name (if omitted, selection menu is shown)",
    )
    arg_parser.add_argument(
        "--dataset",
        default=None,
        help="Dataset selection (e.g., '2', '1,3', 'A', or XML file path)",
    )
    arg_parser.add_argument(
        "--mode",
        choices=["interactive", "automatic"],
        default=None,
        help="Processing mode (if omitted, selection menu is shown)",
    )
    arg_parser.add_argument(
        "--auto-start",
        action="store_true",
        help="Skip menu and start processing immediately",
    )

    args = arg_parser.parse_args()

    print_banner()

    if args.model:
        model_name = args.model
        print(f"\n✅ Selected model: {model_name}")
    else:
        model_name = select_model()

    available_datasets = get_available_datasets()

    if args.dataset:
        selected_datasets = resolve_dataset_argument(args.dataset, available_datasets)
        if not selected_datasets:
            print("❌ No valid datasets resolved from --dataset argument.")
            sys.exit(1)
        _print_dataset_selection(selected_datasets)
    else:
        selected_datasets = select_datasets(available_datasets)
        if not selected_datasets:
            sys.exit(1)

    selected_dataset_files = [dataset["file"] for dataset in selected_datasets]

    if not check_prerequisites(selected_dataset_files):
        sys.exit(1)

    components = setup_components(args.ollama_url, model_name)
    if not components:
        sys.exit(1)

    ollama_client, storage_manager, processor = components

    if args.mode:
        processing_mode = args.mode
    else:
        processing_mode = select_processing_mode()

    loaded_datasets: Dict[str, list] = {}

    if args.auto_start:
        print("\n🚀 Auto-starting question processing...")
        if not process_selected_datasets(
            selected_datasets, loaded_datasets, processor, processing_mode
        ):
            sys.exit(1)
        return

    while True:
        choice = show_menu()

        if choice == "1":
            if not process_selected_datasets(
                selected_datasets, loaded_datasets, processor, processing_mode
            ):
                print("❌ Could not process selected datasets due to loading errors.")

        elif choice == "2":
            summary = storage_manager.get_results_summary()
            print("\n📊 Progress Summary")
            print("-" * 40)
            if summary:
                print(f"Total Processed: {summary.get('total_processed', 0)}")
                print(f"Successful: {summary.get('successful', 0)}")
                print(f"Failed: {summary.get('failed', 0)}")
                if summary.get("average_processing_time", 0) > 0:
                    print(f"Avg Processing Time: {summary['average_processing_time']:.2f}s")

                categories = summary.get("categories", {})
                if categories:
                    print("\nBy Category:")
                    for cat, stats in categories.items():
                        print(f"  {cat}: {stats['successful']}/{stats['total']} successful")
            else:
                print("No results found.")

        elif choice == "3":
            import time

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            if len(selected_datasets) == 1:
                dataset_name = os.path.splitext(
                    os.path.basename(selected_datasets[0]["file"])
                )[0]
            else:
                dataset_name = "multi_dataset"

            csv_file = f"{dataset_name}_results_{timestamp}.csv"

            if storage_manager.export_results_csv(csv_file):
                print(f"✅ Results exported to {csv_file}")
            else:
                print("❌ Failed to export results")

        elif choice == "4":
            test_ollama_connection(ollama_client)

        elif choice == "5":
            for dataset in selected_datasets:
                xml_file = dataset["file"]
                questions = get_dataset_questions(xml_file, loaded_datasets)
                if questions is None:
                    print(f"❌ Failed to load dataset for statistics: {xml_file}")
                    continue

                if len(selected_datasets) > 1:
                    print("\n" + "=" * 60)
                    print(f"📚 Dataset: {dataset['name']}")
                    print(f"📄 File: {xml_file}")
                    print("=" * 60)

                show_question_statistics(questions)

        elif choice == "6":
            print("\n👋 Goodbye!")
            break

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
