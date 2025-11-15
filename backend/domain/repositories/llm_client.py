"""
LLM Client Interface

Abstract interface for Large Language Model interactions.
Provides a clean abstraction layer that allows switching between different LLM providers
(OpenAI, Azure OpenAI, Anthropic, Ollama) without changing application code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM service fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class LLMValidationError(LLMError):
    """Raised when LLM response doesn't match expected schema."""
    pass


class ILLMClient(ABC):
    """
    Abstract interface for LLM client implementations.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across the application.
    """
    
    @abstractmethod
    def extract_structured_data(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Extract structured data from text using LLM with JSON schema validation.
        
        Args:
            prompt: The prompt to send to the LLM
            schema: JSON schema defining the expected output structure
            model: Optional model name (uses default if not specified)
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            
        Returns:
            Dict containing the extracted structured data
            
        Raises:
            LLMConnectionError: If connection to LLM service fails
            LLMRateLimitError: If rate limit is exceeded
            LLMValidationError: If response doesn't match schema
            LLMError: For other LLM-related errors
        """
        pass
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text completion from a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            model: Optional model name (uses default if not specified)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Returns:
            Generated text as string
            
        Raises:
            LLMConnectionError: If connection to LLM service fails
            LLMRateLimitError: If rate limit is exceeded
            LLMError: For other LLM-related errors
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model names/identifiers
            
        Raises:
            LLMConnectionError: If connection to LLM service fails
        """
        pass
