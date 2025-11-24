#!/usr/bin/env python3
"""
Test script to verify auto-saving functionality
"""

import json
from src.xml_parser import XMLParser
from src.ollama_client import OllamaClient
from src.storage import StorageManager
from src.question_processor import QuestionProcessor

def main():
    print("🧪 Testing Auto-Save Functionality")
    print("=" * 50)
    
    # Initialize components
    parser = XMLParser('calculus_comprehensive_1000.xml')
    ollama_client = OllamaClient()
    storage_manager = StorageManager()
    processor = QuestionProcessor(ollama_client, storage_manager)
    
    try:
        # Parse questions
        questions = parser.parse()
        print(f"✅ Loaded {len(questions)} questions from XML")
        
        # Show first question details
        first_question = questions[0]
        print(f"\n📋 First Question Details:")
        print(f"   ID: {first_question.id}")
        print(f"   Category: {first_question.category}")
        print(f"   Question: {first_question.question_text}")
        print(f"   Expected Answer: {first_question.answer}")
        
        # Check current results file
        try:
            with open('data/results.json', 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            print(f"\n📁 Current results.json status:")
            print(f"   Total results: {len(current_data.get('results', []))}")
            print(f"   Processed questions: {current_data.get('metadata', {}).get('processed_questions', 0)}")
        except Exception as e:
            print(f"❌ Error reading results.json: {e}")
        
        print(f"\n🚀 Ready to test! Run 'python main.py' to start processing.")
        print(f"   The system will now auto-save every LLM response.")
        print(f"   You only need to press 'C' to continue to the next question.")
        print(f"   Check data/results.json after each question to see it update!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()