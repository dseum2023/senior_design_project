#!/usr/bin/env python3
"""
Test Expression Verification
Tests the verification system with calculus problems that have expression answers
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.verifier import verify_answer
from src.ollama_client import OllamaClient


def test_expression_verification():
    """Test expression verification with various calculus problems"""
    print("="*80)
    print("🧮 EXPRESSION VERIFICATION TEST")
    print("="*80)
    
    # Test cases with calculus problems that have expression answers
    test_cases = [
        {
            "name": "Derivative Test - Power Rule",
            "problem": "Find the derivative of f(x) = 3x^4 + 2x^2 - 5x + 1",
            "expected_answer": "12x^3 + 4x - 5",
            "alternate_answer": "f'(x) = 12x^3 + 4x - 5"
        },
        {
            "name": "Integral Test - Basic Polynomial",
            "problem": "Find the indefinite integral of 6x^2 + 4x - 3",
            "expected_answer": "2x^3 + 2x^2 - 3x + C",
            "alternate_answer": "2x^3 + 2x^2 - 3x"
        },
        {
            "name": "Chain Rule Test",
            "problem": "Find the derivative of f(x) = (2x + 1)^3",
            "expected_answer": "6(2x + 1)^2",
            "alternate_answer": "6(2x+1)^2"
        },
        {
            "name": "Product Rule Test",
            "problem": "Find the derivative of f(x) = x^2 * sin(x)",
            "expected_answer": "2x*sin(x) + x^2*cos(x)",
            "alternate_answer": "2x sin(x) + x^2 cos(x)"
        }
    ]
    
    # Initialize Ollama client
    print("🤖 Initializing Ollama client...")
    ollama_client = OllamaClient()
    
    # Test connection
    if not ollama_client.test_connection():
        print("❌ Cannot connect to Ollama server. Testing with mock responses...")
        test_with_mock_responses(test_cases)
        return
    
    if not ollama_client.check_model_availability():
        print(f"❌ Model '{ollama_client.model}' not available. Testing with mock responses...")
        test_with_mock_responses(test_cases)
        return
    
    print("✅ Ollama connection established")
    print(f"✅ Model '{ollama_client.model}' is available")
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Problem: {test_case['problem']}")
        print(f"Expected: {test_case['expected_answer']}")
        if test_case['alternate_answer']:
            print(f"Alternate: {test_case['alternate_answer']}")
        
        print(f"\n🔄 Querying LLM...")
        
        # Get LLM response
        response = ollama_client.query_llm(test_case['problem'])
        
        if response.success:
            print(f"✅ LLM Response received ({response.processing_time:.2f}s)")
            print(f"\n🤖 LLM Response:")
            print("-" * 50)
            print(response.response_text)
            print("-" * 50)
            
            # Verify the answer
            print(f"\n🔍 Verifying answer...")
            verification = verify_answer(
                llm_response=response.response_text,
                expected_answer=test_case['expected_answer'],
                alternate_answer=test_case['alternate_answer']
            )
            
            # Display results
            display_verification_result(verification, i)
            
        else:
            print(f"❌ LLM Error: {response.error_message}")
            continue
        
        # Ask user if they want to continue
        if i < len(test_cases):
            choice = input(f"\nContinue to next test? (y/n): ").strip().lower()
            if choice != 'y':
                break
    
    print(f"\n🏁 Expression verification testing complete!")


def test_with_mock_responses(test_cases):
    """Test with mock LLM responses when Ollama is not available"""
    print("\n🧪 Testing with mock LLM responses...")
    
    mock_responses = [
        "Let me solve this step by step.\n\nUsing the power rule for derivatives:\nf(x) = 3x^4 + 2x^2 - 5x + 1\nf'(x) = 3(4x^3) + 2(2x) - 5(1) + 0\nf'(x) = 12x^3 + 4x - 5\n\nFINAL_ANSWER: 12x^3 + 4x - 5",
        "To find the indefinite integral:\n∫(6x^2 + 4x - 3)dx\n= ∫6x^2 dx + ∫4x dx - ∫3 dx\n= 6(x^3/3) + 4(x^2/2) - 3x + C\n= 2x^3 + 2x^2 - 3x + C\n\nFINAL_ANSWER: 2x^3 + 2x^2 - 3x + C",
        "Using the chain rule:\nf(x) = (2x + 1)^3\nLet u = 2x + 1, then f(x) = u^3\nf'(x) = 3u^2 * du/dx = 3(2x + 1)^2 * 2 = 6(2x + 1)^2\n\nFINAL_ANSWER: 6(2x + 1)^2",
        "Using the product rule: (uv)' = u'v + uv'\nLet u = x^2, v = sin(x)\nu' = 2x, v' = cos(x)\nf'(x) = 2x * sin(x) + x^2 * cos(x)\n\nFINAL_ANSWER: 2x*sin(x) + x^2*cos(x)"
    ]
    
    for i, (test_case, mock_response) in enumerate(zip(test_cases, mock_responses), 1):
        print(f"\n{'='*60}")
        print(f"MOCK TEST {i}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Problem: {test_case['problem']}")
        print(f"Expected: {test_case['expected_answer']}")
        
        print(f"\n🤖 Mock LLM Response:")
        print("-" * 50)
        print(mock_response)
        print("-" * 50)
        
        # Verify the answer
        print(f"\n🔍 Verifying answer...")
        verification = verify_answer(
            llm_response=mock_response,
            expected_answer=test_case['expected_answer'],
            alternate_answer=test_case['alternate_answer']
        )
        
        # Display results
        display_verification_result(verification, i)


def display_verification_result(verification, test_num):
    """Display verification result in a formatted way"""
    print(f"\n📊 VERIFICATION RESULT #{test_num}")
    print("=" * 60)
    
    if verification.verification_status == "correct":
        print("✅ [CORRECT] Answer verified successfully!")
        print(f"   Extracted Answer: {verification.extracted_answer}")
        print(f"   Expected Answer:  {verification.expected_normalized.original_text}")
        print(f"   Match Type: {verification.match_type}")
        print(f"   Extraction Method: {verification.extraction_method} (confidence: {verification.extraction_confidence:.1f})")
        if verification.matched_answer == "alternate":
            print(f"   Note: Matched alternate answer")
            
    elif verification.verification_status == "incorrect":
        print("❌ [INCORRECT] Answer does not match!")
        print(f"   Extracted Answer: {verification.extracted_answer}")
        if verification.extracted_normalized:
            print(f"   Extracted Type: {verification.extracted_normalized.answer_type.value}")
        print(f"   Expected Answer:  {verification.expected_normalized.original_text}")
        print(f"   Expected Type: {verification.expected_normalized.answer_type.value}")
        print(f"   Reason: {verification.details}")
        
    elif verification.verification_status == "unable_to_verify":
        print("⚠️  [UNABLE TO VERIFY] Could not extract answer")
        print(f"   Expected Answer: {verification.expected_normalized.original_text}")
        print(f"   Reason: {verification.error_message}")
        
    else:  # error
        print("💥 [ERROR] Verification failed")
        print(f"   Error: {verification.error_message}")
    
    print(f"   Extraction Confidence: {verification.extraction_confidence:.1f}")
    print(f"   Comparison Confidence: {verification.comparison_confidence:.1f}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_expression_verification()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()