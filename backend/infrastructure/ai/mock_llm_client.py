"""
Mock LLM Client for Testing

Provides a mock implementation for dry-run mode without API calls.
"""

from typing import Dict, Any, List, Optional
from domain.repositories.llm_client import ILLMClient


class MockLLMClient(ILLMClient):
    """
    Mock LLM client for dry-run testing.
    
    Returns fake data without making real API calls.
    Useful for testing the pipeline without costs.
    """
    
    def extract_structured_data(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """Return mock structured data."""
        print("[MOCK] LLM extraction simulated (no API call)")
        print(f"[MOCK] Prompt length: {len(prompt)} chars")
        
        # Return mock attendance data
        return {
            "members": [
                {
                    "name": "Peter De Roover",
                    "spoke": True,
                    "confidence": 0.95
                },
                {
                    "name": "Francesca Van Belleghem",
                    "spoke": True,
                    "confidence": 0.88
                },
                {
                    "name": "Kurt Moons",
                    "spoke": False,
                    "confidence": 0.75
                }
            ]
        }
    
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """Return mock text."""
        return "Mock LLM response (dry-run mode)"
    
    def get_available_models(self) -> List[str]:
        """Return mock model list."""
        return ["mock-gpt-4", "mock-gpt-3.5-turbo"]
