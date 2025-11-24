"""
XML Parser for Calculus Questions
Extracts questions from the calculus_comprehensive_1000.xml file
"""

import xml.etree.ElementTree as ET
import json
from typing import List, Dict, Any
import os


class Question:
    """Represents a single calculus question"""
    
    def __init__(self, question_id: str, category: str, question_text: str, answer: str):
        self.id = question_id
        self.category = category
        self.question_text = question_text
        self.answer = answer
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary format"""
        return {
            'id': self.id,
            'category': self.category,
            'question': self.question_text,
            'expected_answer': self.answer
        }
    
    def __str__(self) -> str:
        return f"Question {self.id} ({self.category}): {self.question_text}"


class XMLParser:
    """Parser for the calculus XML file"""
    
    def __init__(self, xml_file_path: str):
        self.xml_file_path = xml_file_path
        self.questions: List[Question] = []
        self.metadata: Dict[str, Any] = {}
    
    def parse(self) -> List[Question]:
        """Parse the XML file and extract all questions"""
        if not os.path.exists(self.xml_file_path):
            raise FileNotFoundError(f"XML file not found: {self.xml_file_path}")
        
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            
            # Extract metadata
            self.metadata = {
                'name': root.get('name', ''),
                'total_problems': int(root.get('total_problems', 0))
            }
            
            # Extract metadata details
            metadata_elem = root.find('metadata')
            if metadata_elem is not None:
                desc_elem = metadata_elem.find('description')
                topics_elem = metadata_elem.find('topics')
                
                if desc_elem is not None:
                    self.metadata['description'] = desc_elem.text
                if topics_elem is not None:
                    self.metadata['topics'] = topics_elem.text
                
                # Extract categories
                categories_elem = metadata_elem.find('categories')
                if categories_elem is not None:
                    categories = {}
                    for category in categories_elem.findall('category'):
                        name = category.get('name', '')
                        count = int(category.get('count', 0))
                        categories[name] = count
                    self.metadata['categories'] = categories
            
            # Extract all problems
            self.questions = []
            for problem in root.findall('problem'):
                question_id = problem.get('id', '')
                category = problem.get('category', '')
                
                question_elem = problem.find('question')
                answer_elem = problem.find('answer')
                
                if question_elem is not None and answer_elem is not None:
                    question_text = question_elem.text.strip() if question_elem.text else ''
                    answer = answer_elem.text.strip() if answer_elem.text else ''
                    
                    question = Question(question_id, category, question_text, answer)
                    self.questions.append(question)
            
            print(f"Successfully parsed {len(self.questions)} questions from XML file")
            return self.questions
            
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error parsing XML: {e}")
    
    def save_questions_cache(self, cache_file_path: str) -> None:
        """Save parsed questions to JSON cache file"""
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        
        cache_data = {
            'metadata': self.metadata,
            'questions': [q.to_dict() for q in self.questions],
            'total_questions': len(self.questions)
        }
        
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"Questions cache saved to: {cache_file_path}")
    
    def load_questions_cache(self, cache_file_path: str) -> List[Question]:
        """Load questions from JSON cache file"""
        if not os.path.exists(cache_file_path):
            raise FileNotFoundError(f"Cache file not found: {cache_file_path}")
        
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        self.metadata = cache_data.get('metadata', {})
        
        self.questions = []
        for q_data in cache_data.get('questions', []):
            question = Question(
                q_data['id'],
                q_data['category'],
                q_data['question'],
                q_data['expected_answer']
            )
            self.questions.append(question)
        
        print(f"Loaded {len(self.questions)} questions from cache")
        return self.questions
    
    def get_questions(self) -> List[Question]:
        """Get the list of parsed questions"""
        return self.questions
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata from the XML file"""
        return self.metadata


def main():
    """Test the XML parser"""
    parser = XMLParser('calculus_comprehensive_1000.xml')
    questions = parser.parse()
    
    print(f"\nMetadata: {parser.get_metadata()}")
    print(f"\nFirst 3 questions:")
    for i, question in enumerate(questions[:3]):
        try:
            print(f"{i+1}. {question}")
        except UnicodeEncodeError:
            # Handle Unicode encoding issues on Windows
            question_text = question.question_text.encode('ascii', 'replace').decode('ascii')
            print(f"{i+1}. Question {question.id} ({question.category}): {question_text}")
    
    # Save cache
    parser.save_questions_cache('data/questions.json')


if __name__ == "__main__":
    main()