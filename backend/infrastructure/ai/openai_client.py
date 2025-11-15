"""
OpenAI Client Implementation

Concrete implementation of ILLMClient for OpenAI's API.
Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
"""

import json
import os
from typing import Dict, Any, List, Optional

try:
    from openai import OpenAI
    import openai
except ImportError:
    raise ImportError("openai package is required. Install with: pip install openai>=1.0.0")

from domain.repositories.llm_client import (
    ILLMClient,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMValidationError
)


class OpenAIClient(ILLMClient):
    """
    OpenAI implementation of the LLM client interface.
    
    Uses OpenAI's Chat Completions API with JSON mode for structured outputs.
    Supports GPT-4, GPT-4-turbo, and GPT-3.5-turbo models.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-4-turbo-preview",
        organization: Optional[str] = None
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            default_model: Default model to use for requests
            organization: Optional organization ID
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.default_model = default_model
        self.client = OpenAI(
            api_key=self.api_key,
            organization=organization
        )
    
    def extract_structured_data(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Extract structured data using OpenAI's JSON mode.
        
        Uses response_format={"type": "json_object"} to ensure valid JSON output.
        """
        try:
            model_to_use = model or self.default_model
            
            # Add schema to system message for guidance
            system_message = (
                "You are a data extraction assistant. Extract information according to the schema. "
                "Always respond with valid JSON matching the provided schema.\n\n"
                f"Schema:\n{json.dumps(schema, indent=2)}"
            )
            
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=temperature
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Log token usage
            usage = response.usage
            print(f"[OpenAI] Tokens used: {usage.total_tokens} "
                  f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
            
            return result
            
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {e}")
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise LLMError(f"OpenAI API error: {e}")
    
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text completion using OpenAI's Chat API.
        """
        try:
            model_to_use = model or self.default_model
            
            kwargs = {
                "model": model_to_use,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            print(f"[OpenAI] Tokens used: {usage.total_tokens} "
                  f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
            
            return content
            
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to OpenAI API: {e}")
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
        except Exception as e:
            raise LLMError(f"OpenAI API error: {e}")
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.
        
        Returns commonly used models without making an API call.
        """
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
