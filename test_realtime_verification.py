"""
Quick test of real-time verification with a single question
"""

import sys
sys.path.insert(0, 'src')

from src.ollama_client import OllamaClient
from src.xml_parser import XMLParser, Question
from src.storage import StorageManager
from src.question_processor import QuestionProcessor

# Create a simple test question
test_question = Question(
    question_id="test_1",
    category="test",
    question_text="What is 2 + 2?",
    answer="4"
)

print("="*60)
print("REAL-TIME VERIFICATION TEST")
print("="*60)
print("\nThis will test the integrated verification system.")
print("It will query the LLM and immediately verify the answer.\n")

# Initialize components
ollama = OllamaClient(model="gpt-oss:20b")
storage = StorageManager()
processor = QuestionProcessor(ollama, storage)

# Process the test question
print("Testing with a simple question: What is 2 + 2?")
print("Expected answer: 4")
print("\n" + "="*60 + "\n")

try:
    processor.total_questions = 1
    processor.process_question(test_question)
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
except Exception as e:
    print(f"\nError during test: {e}")
    import traceback
    traceback.print_exc()
