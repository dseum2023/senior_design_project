"""
Ollama API Client
Handles communication with the local Ollama LLM server
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from the LLM"""
    response_text: str
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    model_used: str = ""


class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma3:4b"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Test if Ollama server is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                for model in models:
                    if model.get('name', '').startswith(self.model):
                        return True
            return False
        except requests.exceptions.RequestException:
            return False
    
    def query_llm(self, question: str, system_prompt: Optional[str] = None, stream_callback=None) -> LLMResponse:
        """
        Send a question to the LLM and get response
        
        Args:
            question: The calculus question to ask
            system_prompt: Optional system prompt to guide the LLM
            stream_callback: Optional callback function for streaming responses
        
        Returns:
            LLMResponse object with the result
        """
        start_time = time.time()
        
        # Default system prompt for math questions with enforced answer format
        if system_prompt is None:
            system_prompt = (
                "You are a mathematics expert. When solving math problems, please:\n\n"
                "1. THINK STEP BY STEP and show ALL your work\n"
                "2. Explain your reasoning clearly at each step\n"
                "3. Show all calculations, substitutions, and algebraic manipulations\n"
                "4. If using formulas, state them explicitly\n"
                "5. Verify your work when possible\n\n"
                "After showing your complete solution process, provide your final answer in this exact format:\n"
                "FINAL_ANSWER: [your answer here]\n\n"
                "Examples of final answer formats:\n"
                "- Numeric answers: FINAL_ANSWER: 42.67\n"
                "- Fractions: FINAL_ANSWER: 54584/99000\n"
                "- Expressions: FINAL_ANSWER: f'(x) = 12x^5\n"
                "- Integrals: FINAL_ANSWER: (9/2)x^2 + C\n"
                "- Text answers: FINAL_ANSWER: Rational\n"
                "- Ranges: FINAL_ANSWER: 5 and 6\n\n"
                "Remember: Show your thinking process first, then provide the final answer!"
            )
        
        # Determine if we should stream
        use_streaming = stream_callback is not None
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "prompt": question,
            "system": system_prompt,
            "stream": use_streaming,
            "options": {
                "temperature": 0.3,  # Slightly higher temperature for more detailed explanations
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2048  # Allow longer responses for detailed work
            }
        }
        
        try:
            if use_streaming:
                # Handle streaming response
                import sys
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120,
                    stream=True
                )

                if response.status_code == 200:
                    full_response = ""
                    chunk_count = 0

                    try:
                        for line in response.iter_lines(decode_unicode=True):
                            if line:
                                try:
                                    chunk_data = json.loads(line)
                                    chunk_text = chunk_data.get('response', '')

                                    if chunk_text:
                                        full_response += chunk_text
                                        chunk_count += 1
                                        
                                        # Call the streaming callback to display progress IMMEDIATELY
                                        if stream_callback:
                                            try:
                                                stream_callback(chunk_text)
                                            except Exception as callback_error:
                                                # Don't let callback errors break streaming
                                                print(f"\nWarning: Streaming callback error: {callback_error}", file=sys.stderr)

                                    # Check if this is the final chunk
                                    if chunk_data.get('done', False):
                                        break

                                except json.JSONDecodeError as e:
                                    # Log JSON decode errors but continue
                                    print(f"\nWarning: JSON decode error in chunk: {e}", file=sys.stderr)
                                    continue
                                    
                    except Exception as stream_error:
                        print(f"\nError during streaming: {stream_error}", file=sys.stderr)
                        # If we got some response, use it
                        if full_response.strip():
                            processing_time = time.time() - start_time
                            return LLMResponse(
                                response_text=full_response.strip(),
                                processing_time=processing_time,
                                success=True,
                                error_message=f"Streaming interrupted: {stream_error}",
                                model_used=self.model
                            )
                        else:
                            raise stream_error
                    
                    processing_time = time.time() - start_time
                    
                    if full_response.strip():
                        return LLMResponse(
                            response_text=full_response.strip(),
                            processing_time=processing_time,
                            success=True,
                            model_used=self.model
                        )
                    else:
                        return LLMResponse(
                            response_text="",
                            processing_time=processing_time,
                            success=False,
                            error_message="Empty response from LLM",
                            model_used=self.model
                        )
                else:
                    processing_time = time.time() - start_time
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    return LLMResponse(
                        response_text="",
                        processing_time=processing_time,
                        success=False,
                        error_message=error_msg,
                        model_used=self.model
                    )
            else:
                # Handle non-streaming response (original behavior)
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=120  # 2 minute timeout for complex calculations
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').strip()
                    
                    if response_text:
                        return LLMResponse(
                            response_text=response_text,
                            processing_time=processing_time,
                            success=True,
                            model_used=self.model
                        )
                    else:
                        return LLMResponse(
                            response_text="",
                            processing_time=processing_time,
                            success=False,
                            error_message="Empty response from LLM",
                            model_used=self.model
                        )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    return LLMResponse(
                        response_text="",
                        processing_time=processing_time,
                        success=False,
                        error_message=error_msg,
                        model_used=self.model
                    )
                
        except requests.exceptions.Timeout:
            processing_time = time.time() - start_time
            return LLMResponse(
                response_text="",
                processing_time=processing_time,
                success=False,
                error_message="Request timed out",
                model_used=self.model
            )
        except requests.exceptions.ConnectionError:
            processing_time = time.time() - start_time
            return LLMResponse(
                response_text="",
                processing_time=processing_time,
                success=False,
                error_message="Could not connect to Ollama server",
                model_used=self.model
            )
        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            return LLMResponse(
                response_text="",
                processing_time=processing_time,
                success=False,
                error_message=f"Request error: {str(e)}",
                model_used=self.model
            )
        except json.JSONDecodeError:
            processing_time = time.time() - start_time
            return LLMResponse(
                response_text="",
                processing_time=processing_time,
                success=False,
                error_message="Invalid JSON response from server",
                model_used=self.model
            )
        except Exception as e:
            processing_time = time.time() - start_time
            return LLMResponse(
                response_text="",
                processing_time=processing_time,
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                model_used=self.model
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Request error: {str(e)}"}


def main():
    """Test the Ollama client"""
    client = OllamaClient()
    
    print("Testing Ollama connection...")
    if client.test_connection():
        print("✓ Ollama server is running")
    else:
        print("✗ Cannot connect to Ollama server")
        return
    
    print(f"\nChecking model availability: {client.model}")
    if client.check_model_availability():
        print("✓ Model is available")
    else:
        print("✗ Model not found")
        return
    
    # Test with a simple calculus question
    test_question = "Find the derivative of x^2 + 3x + 1"
    print(f"\nTesting with question: {test_question}")
    
    response = client.query_llm(test_question)
    
    if response.success:
        print(f"✓ LLM Response ({response.processing_time:.2f}s):")
        print(response.response_text)
    else:
        print(f"✗ Error: {response.error_message}")


if __name__ == "__main__":
    main()