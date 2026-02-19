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
    is_correct: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_question_and_response(cls, question: Question, llm_response: LLMResponse, verification: Optional[Dict[str, Any]] = None) -> 'QuestionResult':
        """Create QuestionResult from Question and LLMResponse objects"""
        is_correct = None
        if isinstance(verification, dict):
            value = verification.get("is_correct")
            if isinstance(value, bool):
                is_correct = value

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
            verification=verification,
            is_correct=is_correct
        )


class StorageManager:
    """Manages storage of questions and results"""
    
    def __init__(self, data_dir: str = "data", results_dir: str = "results"):
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.results_file = os.path.join(results_dir, "results.json")
        self.progress_file = os.path.join(data_dir, "progress.json")
        
        # Ensure required directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()

    def _empty_results_payload(
        self,
        created_iso: Optional[str] = None,
        dataset_file: Optional[str] = None,
        model_name: str = "",
        requested_timestamp: str = "",
        filename_timestamp: str = "",
    ) -> Dict[str, Any]:
        """Build an empty results payload."""
        created_iso = created_iso or datetime.now().isoformat()

        return {
            "summary": {
                "total_time_seconds": 0.0,
                "average_time_per_question_seconds": 0.0,
                "questions_answered": 0,
                "questions_correct": 0,
                "percent_correct": 0.0,
            },
            "metadata": {
                "created": created_iso,
                "requested_timestamp_format": requested_timestamp,
                "filename_timestamp": filename_timestamp,
                "dataset_file": dataset_file,
                "model_name": model_name,
                "total_questions": 0,
                "processed_questions": 0,
                "successful_responses": 0,
                "failed_responses": 0,
                "last_updated": created_iso,
            },
            "results": [],
        }

    def _empty_progress_payload(self, session_start_iso: Optional[str] = None) -> Dict[str, Any]:
        """Build an empty progress payload."""
        session_start_iso = session_start_iso or datetime.now().isoformat()
        return {
            "last_processed_id": None,
            "processed_ids": [],
            "skipped_ids": [],
            "failed_ids": [],
            "session_start": session_start_iso,
        }

    def _filename_timestamp(self, dt: datetime) -> str:
        """
        Build timestamp string for filenames.

        Note: ':' is invalid in Windows filenames, so '-' is used for time separators.
        """
        return dt.strftime("%m-%d-%yT%H-%M-%S")

    def _requested_timestamp(self, dt: datetime) -> str:
        """Build human-readable timestamp in requested format."""
        return dt.strftime("%m-%d-%yT%H:%M:%S")

    def _sanitize_file_component(self, value: str) -> str:
        """Sanitize text for safe use in filenames."""
        return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)

    def _ensure_unique_results_file_path(self, run_name: str) -> str:
        """Ensure result filename is unique within the data directory."""
        base = os.path.join(self.results_dir, f"{run_name}.json")
        if not os.path.exists(base):
            return base

        counter = 1
        while True:
            candidate = os.path.join(self.results_dir, f"{run_name}_{counter:02d}.json")
            if not os.path.exists(candidate):
                return candidate
            counter += 1
    
    def _initialize_files(self):
        """Initialize storage files if they don't exist"""
        if not os.path.exists(self.results_file):
            initial_data = self._empty_results_payload()
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(self.progress_file):
            progress_data = self._empty_progress_payload()
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)

    def start_new_run(
        self,
        run_name: Optional[str] = None,
        dataset_file: Optional[str] = None,
        model_name: str = "",
    ) -> str:
        """
        Start a fresh run by switching to a new results file and resetting progress.

        Args:
            run_name: Optional run name. If not provided, a timestamped name is used.
            dataset_file: Optional dataset file associated with this run.
            model_name: Optional model name used for this run.

        Returns:
            str: Path to the newly created results file.
        """
        created_dt = datetime.now()
        requested_timestamp = self._requested_timestamp(created_dt)
        filename_timestamp = self._filename_timestamp(created_dt)

        if not run_name:
            run_name = f"results_{filename_timestamp}"

        self.results_file = self._ensure_unique_results_file_path(run_name)
        created_iso = created_dt.isoformat()

        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(
                self._empty_results_payload(
                    created_iso=created_iso,
                    dataset_file=dataset_file,
                    model_name=model_name,
                    requested_timestamp=requested_timestamp,
                    filename_timestamp=filename_timestamp,
                ),
                f,
                indent=2,
                ensure_ascii=False,
            )

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self._empty_progress_payload(session_start_iso=created_iso), f, indent=2, ensure_ascii=False)

        return self.results_file

    def start_new_dataset_run(self, dataset_file: str, model_name: str = "") -> str:
        """Start a new run for a specific dataset."""
        dataset_base_name = os.path.splitext(os.path.basename(dataset_file))[0] or "dataset"
        safe_dataset_name = self._sanitize_file_component(dataset_base_name)
        run_name = f"{safe_dataset_name}_{self._filename_timestamp(datetime.now())}"
        return self.start_new_run(
            run_name=run_name,
            dataset_file=dataset_file,
            model_name=model_name,
        )
    
    def save_result(self, result: QuestionResult) -> bool:
        """
        Save a question result to storage

        Args:
            result: QuestionResult object to save

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            results = data.setdefault("results", [])
            results.append(result.to_dict())

            metadata = data.setdefault("metadata", {})
            metadata["processed_questions"] = len(results)
            metadata["last_updated"] = datetime.now().isoformat()

            if result.success:
                metadata["successful_responses"] = metadata.get("successful_responses", 0) + 1
            else:
                metadata["failed_responses"] = metadata.get("failed_responses", 0) + 1

            data["summary"] = self._compute_summary(results)

            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._update_progress(result.question_id, result.success)
            return True

        except Exception as e:
            print(f"Error saving result: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _compute_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute summary metrics for results payload."""
        question_count = len(results)
        total_time = sum(float(result.get("processing_time", 0.0) or 0.0) for result in results)
        average_time = (total_time / question_count) if question_count > 0 else 0.0
        questions_correct = sum(1 for result in results if result.get("is_correct") is True)
        percent_correct = (questions_correct / question_count * 100.0) if question_count > 0 else 0.0

        return {
            "total_time_seconds": total_time,
            "average_time_per_question_seconds": average_time,
            "questions_answered": question_count,
            "questions_correct": questions_correct,
            "percent_correct": percent_correct,
        }

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

            summary = data.get("summary")
            if not summary:
                summary = self._compute_summary(results)

            categories = {}
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
                "total_processed": summary.get("questions_answered", len(results)),
                "successful": metadata.get("successful_responses", 0),
                "failed": metadata.get("failed_responses", 0),
                "average_processing_time": summary.get("average_time_per_question_seconds", 0.0),
                "total_time": summary.get("total_time_seconds", 0.0),
                "questions_correct": summary.get("questions_correct", 0),
                "percent_correct": summary.get("percent_correct", 0.0),
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
                    'error_message', 'model_used', 'is_correct'
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
