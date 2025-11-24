#!/usr/bin/env python3
"""
Calculus LLM Tester - Main Application
Interactive tool for testing calculus questions with local LLM via Ollama
"""

import sys
import os
import argparse
from typing import Optional

# Force unbuffered output for real-time streaming
os.environ['PYTHONUNBUFFERED'] = '1'

# Configure stdout for immediate flushing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.storage import StorageManager
from src.question_processor import QuestionProcessor


def print_banner():
    """Print application banner"""
    print("="*60)
    print("🧮 MATH LLM TESTER")
    print("="*60)
    print("Interactive tool for testing math questions with LLM")
    print("Model: gpt-oss:20b via Ollama")
    print("="*60)


def get_available_datasets():
    """Get list of available dataset XML files"""
    datasets = {
        '1': {
            'file': 'calculus1_problems.xml',
            'name': 'Calculus 1',
            'description': 'Comprehensive calculus problems'
        },
        '2': {
            'file': 'advanced_probability_statistics_problems.xml',
            'name': 'Probability & Statistics',
            'description': 'Advanced probability and statistics problems'
        },
        '3': {
            'file': 'grade_8_math_problems.xml',
            'name': 'Grade 8 Math',
            'description': 'Grade 8 mathematics problems'
        }
    }

    # Check which datasets actually exist
    available = {}
    for key, dataset in datasets.items():
        if os.path.exists(dataset['file']):
            available[key] = dataset

    return available


def select_dataset():
    """Prompt user to select a dataset"""
    print("\n" + "="*60)
    print("📚 DATASET SELECTION")
    print("="*60)

    datasets = get_available_datasets()

    if not datasets:
        print("❌ No dataset XML files found!")
        print("Please ensure at least one of these files exists:")
        print("  - calculus1_problems.xml")
        print("  - advanced_probability_statistics_problems.xml")
        print("  - grade_8_math_problems.xml")
        return None

    print("\nAvailable datasets:")
    for key, dataset in datasets.items():
        print(f"{key}. {dataset['name']}")
        print(f"   {dataset['description']}")
        print(f"   File: {dataset['file']}")
        print()

    while True:
        choice = input(f"Select dataset (1-{len(datasets)}): ").strip()
        if choice in datasets:
            selected = datasets[choice]
            print(f"\n✅ Selected: {selected['name']}")
            return selected['file']
        print(f"Invalid choice. Please enter a number between 1 and {len(datasets)}.")


def check_prerequisites(xml_file: str) -> bool:
    """Check if all prerequisites are met"""
    print("\n🔍 Checking prerequisites...")

    # Check if XML file exists
    if not os.path.exists(xml_file):
        print(f"❌ XML file not found: {xml_file}")
        print("Please ensure the dataset XML file is in the current directory.")
        return False

    print(f"✅ Found XML file: {xml_file}")
    return True


def setup_components(ollama_url: str, model_name: str, xml_file: str) -> tuple:
    """
    Set up all application components

    Args:
        ollama_url: URL for Ollama server
        model_name: Name of the LLM model to use
        xml_file: Path to the XML dataset file

    Returns:
        Tuple of (parser, ollama_client, storage_manager, processor) or None if setup fails
    """
    try:
        # Initialize XML parser
        print(f"📖 Initializing XML parser for {xml_file}...")
        parser = XMLParser(xml_file)

        # Initialize Ollama client
        print(f"🤖 Initializing Ollama client (URL: {ollama_url}, Model: {model_name})...")
        ollama_client = OllamaClient(base_url=ollama_url, model=model_name)

        # Initialize storage manager
        print("💾 Initializing storage manager...")
        storage_manager = StorageManager()

        # Initialize question processor
        print("⚙️  Initializing question processor...")
        processor = QuestionProcessor(ollama_client, storage_manager)

        return parser, ollama_client, storage_manager, processor

    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return None


def load_questions(parser: XMLParser) -> Optional[list]:
    """Load questions from XML file or cache"""
    cache_file = "data/questions.json"
    
    try:
        # Try to load from cache first
        if os.path.exists(cache_file):
            print("📂 Loading questions from cache...")
            questions = parser.load_questions_cache(cache_file)
        else:
            print("📖 Parsing XML file...")
            questions = parser.parse()
            print("💾 Saving questions cache...")
            parser.save_questions_cache(cache_file)
        
        print(f"✅ Loaded {len(questions)} questions")
        
        # Display metadata
        metadata = parser.get_metadata()
        if metadata:
            print(f"📊 Dataset: {metadata.get('name', 'Unknown')}")
            print(f"📝 Description: {metadata.get('description', 'N/A')}")
            print(f"🏷️  Topics: {metadata.get('topics', 'N/A')}")
            
            categories = metadata.get('categories', {})
            if categories:
                print(f"📂 Categories: {len(categories)} categories")
                # Show top 5 categories by count
                sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                for cat, count in sorted_cats:
                    print(f"   • {cat}: {count} questions")
        
        return questions
        
    except Exception as e:
        print(f"❌ Error loading questions: {e}")
        return None


def show_menu() -> str:
    """Show main menu and get user choice"""
    print("\n" + "="*50)
    print("📋 MAIN MENU")
    print("="*50)
    print("1. Start processing questions")
    print("2. Show progress summary")
    print("3. Export results to CSV")
    print("4. Test Ollama connection")
    print("5. Show question statistics")
    print("6. Exit")
    print("="*50)
    
    while True:
        choice = input("Select option (1-6): ").strip()
        if choice in ['1', '2', '3', '4', '5', '6']:
            return choice
        print("Invalid choice. Please enter a number between 1 and 6.")


def test_ollama_connection(ollama_client: OllamaClient) -> None:
    """Test Ollama connection and model availability"""
    print("\n🔧 Testing Ollama Connection...")
    print("-" * 40)
    
    # Test connection
    if ollama_client.test_connection():
        print("✅ Ollama server is running")
    else:
        print("❌ Cannot connect to Ollama server")
        print(f"   URL: {ollama_client.base_url}")
        print("   Please ensure Ollama is running and accessible.")
        return
    
    # Test model availability
    if ollama_client.check_model_availability():
        print(f"✅ Model '{ollama_client.model}' is available")
    else:
        print(f"❌ Model '{ollama_client.model}' is not available")
        print("   Please install the model using: ollama pull gpt-oss:20b")
        return
    
    # Test with a simple question
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
    
    # Count by category
    categories = {}
    for question in questions:
        cat = question.category
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"Total Questions: {len(questions)}")
    print(f"Categories: {len(categories)}")
    print("\nQuestions by Category:")
    
    # Sort categories by count
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    for category, count in sorted_cats:
        percentage = (count / len(questions)) * 100
        print(f"  {category:25} {count:4d} ({percentage:5.1f}%)")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="Math LLM Tester")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                       help="Ollama server URL (default: http://localhost:11434)")
    parser.add_argument("--model", default="gpt-oss:20b",
                       help="LLM model name (default: gpt-oss:20b)")
    parser.add_argument("--dataset", default=None,
                       help="Dataset XML file to use (skips selection menu)")
    parser.add_argument("--auto-start", action="store_true",
                       help="Skip menu and start processing immediately")

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Select dataset
    if args.dataset:
        xml_file = args.dataset
        print(f"\n📊 Using dataset: {xml_file}")
    else:
        xml_file = select_dataset()
        if not xml_file:
            sys.exit(1)

    # Check prerequisites
    if not check_prerequisites(xml_file):
        sys.exit(1)

    # Setup components
    components = setup_components(args.ollama_url, args.model, xml_file)
    if not components:
        sys.exit(1)

    xml_parser, ollama_client, storage_manager, processor = components

    # Load questions
    questions = load_questions(xml_parser)
    if not questions:
        sys.exit(1)

    # Auto-start if requested
    if args.auto_start:
        print("\n🚀 Auto-starting question processing...")
        processor.process_questions(questions)
        return

    # Main menu loop
    while True:
        choice = show_menu()
        
        if choice == '1':  # Start processing
            processor.process_questions(questions)
        
        elif choice == '2':  # Show progress summary
            summary = storage_manager.get_results_summary()
            print("\n📊 Progress Summary")
            print("-" * 40)
            if summary:
                print(f"Total Processed: {summary.get('total_processed', 0)}")
                print(f"Successful: {summary.get('successful', 0)}")
                print(f"Failed: {summary.get('failed', 0)}")
                if summary.get('average_processing_time', 0) > 0:
                    print(f"Avg Processing Time: {summary['average_processing_time']:.2f}s")
                
                categories = summary.get('categories', {})
                if categories:
                    print("\nBy Category:")
                    for cat, stats in categories.items():
                        print(f"  {cat}: {stats['successful']}/{stats['total']} successful")
            else:
                print("No results found.")
        
        elif choice == '3':  # Export to CSV
            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            # Extract dataset name from xml_file
            dataset_name = os.path.splitext(os.path.basename(xml_file))[0]
            csv_file = f"{dataset_name}_results_{timestamp}.csv"

            if storage_manager.export_results_csv(csv_file):
                print(f"✅ Results exported to {csv_file}")
            else:
                print("❌ Failed to export results")
        
        elif choice == '4':  # Test connection
            test_ollama_connection(ollama_client)
        
        elif choice == '5':  # Show statistics
            show_question_statistics(questions)
        
        elif choice == '6':  # Exit
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