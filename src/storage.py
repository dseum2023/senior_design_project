"""
Storage System for Questions and Results
Handles JSON-based persistence of questions and LLM responses
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from src.xml_parser import Question
from src.ollama_client import LLMResponse


@dataclass
class QuestionResult:
    """Represents a processed question with LLM response"""
    question_id: str
    category: str
    question_text: str
    expected_answer: str
    llm_response: str
    processing_time: float
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    model_used: str = ""
    alternate_answer: Optional[str] = None
    verification: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_question_and_response(cls, question: Question, llm_response: LLMResponse, verification: Optional[Dict[str, Any]] = None) -> 'QuestionResult':
        """Create QuestionResult from Question and LLMResponse objects"""
        return cls(
            question_id=question.id,
            category=question.category,
            question_text=question.question_text,
            expected_answer=question.answer,
            llm_response=llm_response.response_text,
            processing_time=llm_response.processing_time,
            timestamp=datetime.now().isoformat(),
            success=llm_response.success,
            error_message=llm_response.error_message,
            model_used=llm_response.model_used,
            alternate_answer=getattr(question, 'alternate_answer', None),
            verification=verification
        )


class StorageManager:
    """Manages storage of questions and results"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.results_file = os.path.join(data_dir, "results.json")
        self.progress_file = os.path.join(data_dir, "progress.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize storage files if they don't exist"""
        if not os.path.exists(self.results_file):
            initial_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "total_questions": 0,
                    "processed_questions": 0,
                    "successful_responses": 0,
                    "failed_responses": 0
                },
                "results": []
            }
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(self.progress_file):
            progress_data = {
                "last_processed_id": None,
                "processed_ids": [],
                "skipped_ids": [],
                "failed_ids": [],
                "session_start": datetime.now().isoformat()
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def save_result(self, result: QuestionResult) -> bool:
        """
        Save a question result to storage
        
        Args:
            result: QuestionResult object to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            print(f"📁 StorageManager: Attempting to save result for question {result.question_id}")
            print(f"   File path: {self.results_file}")
            print(f"   Result success: {result.success}")
            print(f"   LLM response preview: {result.llm_response[:100]}...")
            
            # Load existing data
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"   Current results count: {len(data.get('results', []))}")
            
            # Add new result
            result_dict = result.to_dict()
            data["results"].append(result_dict)
            
            # Update metadata
            data["metadata"]["processed_questions"] = len(data["results"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            if result.success:
                data["metadata"]["successful_responses"] = data["metadata"].get("successful_responses", 0) + 1
            else:
                data["metadata"]["failed_responses"] = data["metadata"].get("failed_responses", 0) + 1
            
            print(f"   New results count: {len(data['results'])}")
            print(f"   Metadata updated: {data['metadata']['processed_questions']} processed")
            
            # Save updated data
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ File written successfully")
            
            # Update progress
            self._update_progress(result.question_id, result.success)
            
            print(f"   ✅ Progress updated")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving result: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _update_progress(self, question_id: str, success: bool):
        """Update progress tracking"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            progress["last_processed_id"] = question_id
            progress["last_updated"] = datetime.now().isoformat()
            
            if question_id not in progress["processed_ids"]:
                progress["processed_ids"].append(question_id)
            
            if not success and question_id not in progress["failed_ids"]:
                progress["failed_ids"].append(question_id)
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error updating progress: {e}")
    
    def mark_question_skipped(self, question_id: str):
        """Mark a question as skipped"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            if question_id not in progress["skipped_ids"]:
                progress["skipped_ids"].append(question_id)
            
            progress["last_updated"] = datetime.now().isoformat()
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error marking question as skipped: {e}")
    
    def get_processed_question_ids(self) -> List[str]:
        """Get list of already processed question IDs"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress.get("processed_ids", [])
        except Exception:
            return []
    
    def get_skipped_question_ids(self) -> List[str]:
        """Get list of skipped question IDs"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress.get("skipped_ids", [])
        except Exception:
            return []
    
    def get_last_processed_id(self) -> Optional[str]:
        """Get the ID of the last processed question"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress.get("last_processed_id")
        except Exception:
            return None
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get summary statistics of processed results"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            results = data.get("results", [])
            
            # Calculate additional statistics
            categories = {}
            avg_processing_time = 0
            
            if results:
                total_time = sum(r.get("processing_time", 0) for r in results)
                avg_processing_time = total_time / len(results)
                
                for result in results:
                    category = result.get("category", "unknown")
                    if category not in categories:
                        categories[category] = {"total": 0, "successful": 0, "failed": 0}
                    
                    categories[category]["total"] += 1
                    if result.get("success", False):
                        categories[category]["successful"] += 1
                    else:
                        categories[category]["failed"] += 1
            
            return {
                "total_processed": len(results),
                "successful": metadata.get("successful_responses", 0),
                "failed": metadata.get("failed_responses", 0),
                "average_processing_time": avg_processing_time,
                "categories": categories,
                "last_updated": metadata.get("last_updated"),
                "session_start": metadata.get("created")
            }
            
        except Exception as e:
            print(f"Error getting results summary: {e}")
            return {}
    
    def get_result_by_id(self, question_id: str) -> Optional[QuestionResult]:
        """Get a specific result by question ID"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for result_data in data.get("results", []):
                if result_data.get("question_id") == question_id:
                    return QuestionResult(**result_data)
            
            return None
            
        except Exception as e:
            print(f"Error getting result by ID: {e}")
            return None
    
    def export_results_csv(self, output_file: str) -> bool:
        """Export results to CSV format"""
        try:
            import csv
            
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", [])
            
            if not results:
                print("No results to export")
                return False
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'question_id', 'category', 'question_text', 'expected_answer',
                    'llm_response', 'processing_time', 'timestamp', 'success',
                    'error_message', 'model_used'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow(result)
            
            print(f"Results exported to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


def main():
    """Test the storage system"""
    storage = StorageManager()
    
    # Test saving a dummy result
    from src.xml_parser import Question
    from src.ollama_client import LLMResponse
    
    test_question = Question("1", "limits", "Find the limit of x^2 as x approaches 2", "4")
    test_response = LLMResponse("The limit is 4", 1.5, True, model_used="gpt-oss:20b")
    
    result = QuestionResult.from_question_and_response(test_question, test_response)
    
    if storage.save_result(result):
        print("✓ Test result saved successfully")
    else:
        print("✗ Failed to save test result")
    
    # Test getting summary
    summary = storage.get_results_summary()
    print(f"\nResults Summary: {summary}")


if __name__ == "__main__":
    main()