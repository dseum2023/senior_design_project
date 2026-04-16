"""
Interactive Question Processor
Handles the interactive processing of questions with manual confirmation
"""

import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from src.xml_parser import Question
from src.ollama_client import OllamaClient, LLMResponse
from src.storage import StorageManager, QuestionResult
from src.verifier import verify_answer
from src.resource_monitor import ResourceMonitor

if TYPE_CHECKING:
    from src.fairness_controller import FairnessController


class QuestionProcessor:
    """Interactive processor for calculus questions"""
    
    def __init__(
        self,
        ollama_client: OllamaClient,
        storage_manager: StorageManager,
        fairness_controller: Optional['FairnessController'] = None,
    ):
        self.ollama_client = ollama_client
        self.storage_manager = storage_manager
        self.fairness_controller = fairness_controller
        self._fairness_snapshot: Optional[Dict[str, Any]] = None
        self.current_question_index = 0
        self.total_questions = 0
        self.processed_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        # Verification stats
        self.verification_stats = {"correct": 0, "incorrect": 0, "unable_to_verify": 0, "total": 0}
        self.resource_monitor = ResourceMonitor(sample_interval=0.5)
    
    def initialize_session(self, questions: List[Question]) -> bool:
        """
        Initialize processing session
        
        Args:
            questions: List of questions to process
            
        Returns:
            bool: True if initialization successful
        """
        self.total_questions = len(questions)
        
        # Check Ollama connection
        if not self.ollama_client.test_connection():
            print("❌ Cannot connect to Ollama server. Please ensure Ollama is running.")
            return False
        
        # Check model availability
        if not self.ollama_client.check_model_availability():
            print(f"❌ Model '{self.ollama_client.model}' is not available.")
            print("Please ensure the model is installed in Ollama.")
            return False
        
        print("✅ Ollama connection established")
        print(f"✅ Model '{self.ollama_client.model}' is available")

        # Run fairness setup if controller is active
        if self.fairness_controller is not None:
            self.fairness_controller.validate_system_state()
            self.fairness_controller.unload_models(self.ollama_client)
            self.fairness_controller.warmup_model(self.ollama_client)
            self._fairness_snapshot = self.fairness_controller.get_fairness_snapshot()

        # Find starting point based on progress
        processed_ids = self.storage_manager.get_processed_question_ids()
        skipped_ids = self.storage_manager.get_skipped_question_ids()
        
        # Find first unprocessed question
        for i, question in enumerate(questions):
            if question.id not in processed_ids and question.id not in skipped_ids:
                self.current_question_index = i
                break
        else:
            # All questions have been processed or skipped
            self.current_question_index = len(questions)
        
        self.processed_count = len(processed_ids)
        self.skipped_count = len(skipped_ids)
        
        if self.current_question_index < len(questions):
            print(f"📍 Resuming from question #{questions[self.current_question_index].id}")
        else:
            print("🎉 All questions have been processed!")
        
        return True
    
    def display_question(self, question: Question, question_number: int) -> None:
        """Display a question in a formatted way"""
        print("\n" + "="*80)
        print(f"Question #{question.id} ({question_number}/{self.total_questions})")
        print(f"Category: {question.category}")
        print("-" * 80)
        print(f"Question: {question.question_text}")
        print(f"Expected Answer: {question.answer}")
        print("="*80)
    
    def display_llm_response(self, response: LLMResponse) -> None:
        """Display LLM response in a formatted way"""
        print("\n" + "🤖 LLM Response:")
        print("-" * 50)
        if response.success:
            print(response.response_text)
            print(f"\n⏱️  Processing Time: {response.processing_time:.2f} seconds")
            print(f"🔧 Model: {response.model_used}")
        else:
            print(f"❌ Error: {response.error_message}")
            print(f"⏱️  Time: {response.processing_time:.2f} seconds")
        print("-" * 50)
    
    def get_user_choice(self) -> str:
        """Get user choice for next action"""
        print("\nOptions:")
        print("  [C] Continue to next question (result already saved)")
        print("  [R] Retry this question with new LLM response")
        print("  [Q] Quit and save progress")
        print("  [I] Show progress info")
        
        while True:
            choice = input("\nYour choice: ").strip().upper()
            if choice in ['C', 'R', 'Q', 'I']:
                return choice
            print("Invalid choice. Please enter C, R, Q, or I.")
    
    def show_progress_info(self) -> None:
        """Display current progress information"""
        print("\n" + "📊 Progress Information:")
        print("-" * 40)
        print(f"Total Questions: {self.total_questions}")
        print(f"Processed: {self.processed_count}")
        print(f"Skipped: {self.skipped_count}")
        print(f"Remaining: {self.total_questions - self.processed_count - self.skipped_count}")

        if self.total_questions > 0:
            progress_percent = ((self.processed_count + self.skipped_count) / self.total_questions) * 100
            print(f"Progress: {progress_percent:.1f}%")

        # Show verification stats
        if self.verification_stats["total"] > 0:
            print("\nVerification Stats:")
            total_verified = self.verification_stats["correct"] + self.verification_stats["incorrect"]
            if total_verified > 0:
                accuracy = (self.verification_stats["correct"] / total_verified) * 100
                print(f"  Accuracy: {self.verification_stats['correct']}/{total_verified} ({accuracy:.1f}%)")
            print(f"  Correct: {self.verification_stats['correct']}")
            print(f"  Incorrect: {self.verification_stats['incorrect']}")
            print(f"  Unable to Verify: {self.verification_stats['unable_to_verify']}")

        # Get detailed summary from storage
        summary = self.storage_manager.get_results_summary()
        if summary:
            print(f"\nLLM Response Stats:")
            print(f"  Successful Responses: {summary.get('successful', 0)}")
            print(f"  Failed Responses: {summary.get('failed', 0)}")
            if summary.get('average_processing_time', 0) > 0:
                print(f"  Average Processing Time: {summary['average_processing_time']:.2f}s")
        print("-" * 40)
    
    def _streaming_callback(self, chunk: str):
        """Callback function for streaming LLM responses"""
        import sys
        import os
        
        # Write directly to stdout with immediate flush
        sys.stdout.write(chunk)
        sys.stdout.flush()
        
        # Force OS-level flush for Windows compatibility
        if hasattr(os, 'fsync'):
            try:
                os.fsync(sys.stdout.fileno())
            except (OSError, AttributeError):
                pass  # Ignore if not supported

    def display_verification_result(self, verification, llm_response_text: str = None) -> None:
        """Display verification result in a formatted way"""
        print("\n" + "=" * 80)
        print("ANSWER VERIFICATION")
        print("=" * 80)

        if verification.verification_status == "correct":
            print("[CORRECT] Answer verified successfully!")
            print(f"  Extracted Answer: {verification.extracted_answer}")
            print(f"  Expected Answer:  {verification.expected_normalized.original_text}")
            print(f"  Match Type: {verification.match_type}")
            print(f"  Extraction Method: {verification.extraction_method} (confidence: {verification.extraction_confidence:.1f})")
            if verification.matched_answer == "alternate":
                print(f"  Note: Matched alternate answer")

        elif verification.verification_status == "incorrect":
            print("[INCORRECT] Answer does not match!")
            print(f"  Extracted Answer: {verification.extracted_answer} ({verification.extracted_normalized.answer_type.value if verification.extracted_normalized else 'unknown'})")
            print(f"  Expected Answer:  {verification.expected_normalized.original_text} ({verification.expected_normalized.answer_type.value})")
            print(f"  Reason: {verification.details}")

        elif verification.verification_status == "unable_to_verify":
            print("[UNABLE TO VERIFY] Could not extract answer")
            print(f"  Expected Answer: {verification.expected_normalized.original_text}")
            print(f"  Reason: {verification.error_message}")

        else:  # error
            print("[ERROR] Verification failed")
            print(f"  Error: {verification.error_message}")

        # Show running accuracy
        total_verified = self.verification_stats["correct"] + self.verification_stats["incorrect"]
        if total_verified > 0:
            accuracy = (self.verification_stats["correct"] / total_verified) * 100
            print(f"\nRunning Accuracy: {self.verification_stats['correct']}/{total_verified} ({accuracy:.1f}%)")
            if self.verification_stats["unable_to_verify"] > 0:
                print(f"  [{self.verification_stats['unable_to_verify']} unverified]")

        # Optionally show the full LLM response for review (skip if None to avoid duplication)
        if llm_response_text:
            print("\n" + "-" * 80)
            print("LLM WORK (for review):")
            print("-" * 80)
            print(llm_response_text)
            print("-" * 80)

        print("=" * 80)
    
    def process_question(self, question: Question) -> Tuple[bool, bool]:
        """
        Process a single question
        
        Args:
            question: Question to process
            
        Returns:
            Tuple[bool, bool]: (continue_processing, question_was_processed)
        """
        question_number = self.current_question_index + 1
        self.display_question(question, question_number)
        
        # Query the LLM once
        response = None
        
        while True:
            # Only query LLM if we don't have a response yet or user chose retry
            if response is None:
                # Query the LLM with streaming
                print("\n🔄 Querying LLM...")
                print("\n🤖 LLM Response (streaming):")
                print("-" * 50)
                
                # Query with streaming callback to show real-time thinking
                with self.resource_monitor:
                    response = self.ollama_client.query_llm(
                        question.question_text,
                        stream_callback=self._streaming_callback
                    )
                resource_metrics = self.resource_monitor.get_metrics()

                print()  # New line after streaming content
                print("-" * 50)

                # Display final response summary
                if response.success:
                    print(f"⏱️  Processing Time: {response.processing_time:.2f} seconds")
                    print(f"🔧 Model: {response.model_used}")
                else:
                    print(f"❌ Error: {response.error_message}")
                    print(f"⏱️  Time: {response.processing_time:.2f} seconds")
                if resource_metrics:
                    print(f"📊 GPU: {resource_metrics.gpu_util_avg_percent}% util, "
                          f"{resource_metrics.gpu_vram_peak_mb:.0f} MB VRAM, "
                          f"{resource_metrics.gpu_power_avg_w:.1f}W avg")
                    print(f"   CPU: {resource_metrics.cpu_avg_percent}% avg | "
                          f"RAM: {resource_metrics.ram_peak_mb:.0f} MB peak | "
                          f"Energy: {resource_metrics.energy_estimate_wh:.4f} Wh")
                if response.ollama_metrics:
                    om = response.ollama_metrics
                    print(f"   Tokens: {om.get('eval_count', 0)} generated @ "
                          f"{om.get('generation_speed_tps', 0):.1f} tok/s | "
                          f"Prompt: {om.get('prompt_eval_count', 0)} @ "
                          f"{om.get('prompt_processing_speed_tps', 0):.1f} tok/s")
                print("-" * 50)
            
            # Verify the answer automatically
            verification = None
            verification_dict = None

            if response.success:
                print("\n🔍 Verifying answer...")
                verification = verify_answer(
                    llm_response=response.response_text,
                    expected_answer=question.answer,
                    alternate_answer=getattr(question, 'alternate_answer', None)
                )

                # Update verification stats
                self.verification_stats["total"] += 1
                if verification.verification_status == "correct":
                    self.verification_stats["correct"] += 1
                elif verification.verification_status == "incorrect":
                    self.verification_stats["incorrect"] += 1
                elif verification.verification_status == "unable_to_verify":
                    self.verification_stats["unable_to_verify"] += 1

                # Display verification result without showing the full LLM response again
                # after stats update so running accuracy reflects this question.
                self.display_verification_result(verification, llm_response_text=None)

                # Convert verification to dict for storage
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
                    "verification_status": verification.verification_status
                }

            # Auto-save the result immediately after getting LLM response
            print(f"\n💾 Auto-saving result for question {question.id}...")

            result = QuestionResult.from_question_and_response(
                question, response, verification_dict,
                system_metrics=resource_metrics.to_dict() if resource_metrics else None,
                fairness_metadata=self._fairness_snapshot,
            )

            if self.storage_manager.save_result(result):
                print("✅ Result auto-saved successfully to data/results.json")
                self.processed_count += 1
            else:
                print("⚠️  Warning: Failed to auto-save result")

            # Get user choice
            choice = self.get_user_choice()
            
            if choice == 'C':  # Continue
                return True, True
            
            elif choice == 'R':  # Retry
                print("🔄 Retrying question...")
                response = None  # Reset response to trigger new LLM query
                continue
            
            elif choice == 'Q':  # Quit
                print("💾 Saving progress and exiting...")
                return False, False
            
            elif choice == 'I':  # Info
                self.show_progress_info()
                # Don't reset response, just continue to ask for choice again
                continue
    
    def process_questions(self, questions: List[Question]) -> None:
        """
        Process questions interactively
        
        Args:
            questions: List of questions to process
        """
        if not self.initialize_session(questions):
            return
        
        print(f"\n🚀 Starting interactive question processing")
        print(f"📚 Total questions: {self.total_questions}")
        
        if self.current_question_index >= len(questions):
            print("🎉 All questions have been processed or skipped!")
            self.show_progress_info()
            return
        
        # Process questions starting from current index
        for i in range(self.current_question_index, len(questions)):
            self.current_question_index = i
            question = questions[i]
            
            continue_processing, question_processed = self.process_question(question)
            
            if not continue_processing:
                break
        
        # Show final summary
        print("\n🏁 Session Complete!")
        self.show_progress_info()
        
        # Offer to export results
        if self.processed_count > 0:
            export_choice = input("\nWould you like to export results to CSV? (y/n): ").strip().lower()
            if export_choice == 'y':
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                csv_file = f"calculus_results_{timestamp}.csv"
                if self.storage_manager.export_results_csv(csv_file):
                    print(f"✅ Results exported to {csv_file}")
                else:
                    print("❌ Failed to export results")

    def process_questions_auto(self, questions: List[Question]) -> None:
        """
        Process questions automatically and sequentially without per-question prompts

        Args:
            questions: List of questions to process
        """
        if not self.initialize_session(questions):
            return

        print(f"\n🚀 Starting automatic sequential processing")
        print(f"📚 Total questions: {self.total_questions}")

        if self.current_question_index >= len(questions):
            print("🎉 All questions have been processed or skipped!")
            self.show_progress_info()
            return

        for i in range(self.current_question_index, len(questions)):
            self.current_question_index = i
            question = questions[i]

            question_number = self.current_question_index + 1
            self.display_question(question, question_number)

            print("\n🔄 Querying LLM...")
            print("\n🤖 LLM Response (streaming):")
            print("-" * 50)
            with self.resource_monitor:
                response = self.ollama_client.query_llm(
                    question.question_text,
                    stream_callback=self._streaming_callback
                )
            resource_metrics = self.resource_monitor.get_metrics()
            print()
            print("-" * 50)

            if response.success:
                print(f"⏱️  Processing Time: {response.processing_time:.2f} seconds")
                print(f"🔧 Model: {response.model_used}")
            else:
                print(f"❌ Error: {response.error_message}")
                print(f"⏱️  Time: {response.processing_time:.2f} seconds")
            if resource_metrics:
                print(f"📊 GPU: {resource_metrics.gpu_util_avg_percent}% util, "
                      f"{resource_metrics.gpu_vram_peak_mb:.0f} MB VRAM, "
                      f"{resource_metrics.gpu_power_avg_w:.1f}W avg")
                print(f"   CPU: {resource_metrics.cpu_avg_percent}% avg | "
                      f"RAM: {resource_metrics.ram_peak_mb:.0f} MB peak | "
                      f"Energy: {resource_metrics.energy_estimate_wh:.4f} Wh")
            if response.ollama_metrics:
                om = response.ollama_metrics
                print(f"   Tokens: {om.get('eval_count', 0)} generated @ "
                      f"{om.get('generation_speed_tps', 0):.1f} tok/s | "
                      f"Prompt: {om.get('prompt_eval_count', 0)} @ "
                      f"{om.get('prompt_processing_speed_tps', 0):.1f} tok/s")
            print("-" * 50)

            verification_dict = None
            if response.success:
                print("\n🔍 Verifying answer...")
                verification = verify_answer(
                    llm_response=response.response_text,
                    expected_answer=question.answer,
                    alternate_answer=getattr(question, 'alternate_answer', None)
                )
                self.verification_stats["total"] += 1
                if verification.verification_status == "correct":
                    self.verification_stats["correct"] += 1
                elif verification.verification_status == "incorrect":
                    self.verification_stats["incorrect"] += 1
                elif verification.verification_status == "unable_to_verify":
                    self.verification_stats["unable_to_verify"] += 1

                # Show verification after stat update so running accuracy is in sync.
                self.display_verification_result(verification, llm_response_text=None)

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
                    "verification_status": verification.verification_status
                }

            # Optional between-question cooldown (default 0s = disabled)
            if self.fairness_controller is not None:
                cfg_cooldown = self.fairness_controller._config.get("cooldown", {})
                if cfg_cooldown.get("between_questions_seconds", 0) > 0:
                    self.fairness_controller.wait_for_cooldown("between_questions")

            print(f"\n💾 Auto-saving result for question {question.id}...")
            result = QuestionResult.from_question_and_response(
                question, response, verification_dict,
                system_metrics=resource_metrics.to_dict() if resource_metrics else None,
                fairness_metadata=self._fairness_snapshot,
            )
            if self.storage_manager.save_result(result):
                print("✅ Result auto-saved successfully to data/results.json")
                self.processed_count += 1
            else:
                print("⚠️  Warning: Failed to auto-save result")

        print("\n🏁 Automatic session complete!")
        self.show_progress_info()


def main():
    """Test the question processor"""
    from src.xml_parser import XMLParser
    
    # Initialize components
    parser = XMLParser('calculus_comprehensive_1000.xml')
    ollama_client = OllamaClient()
    storage_manager = StorageManager()
    processor = QuestionProcessor(ollama_client, storage_manager)
    
    # Parse questions
    try:
        questions = parser.parse()
        print(f"Loaded {len(questions)} questions")
        
        # Process first few questions for testing
        test_questions = questions[:3]  # Only process first 3 for testing
        processor.process_questions(test_questions)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()