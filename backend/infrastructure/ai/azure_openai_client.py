"""
Azure OpenAI Client Implementation

Concrete implementation of ILLMClient for Azure OpenAI Service.
Uses Azure-hosted OpenAI models with enterprise features.
"""

import json
import os
from typing import Dict, Any, List, Optional

try:
    from openai import AzureOpenAI
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


class AzureOpenAIClient(ILLMClient):
    """
    Azure OpenAI implementation of the LLM client interface.
    
    Uses Azure OpenAI Service with deployment names instead of model names.
    Provides enterprise features like EU data residency and SLA guarantees.
    """
    
    def __init__(
        self,
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        default_deployment: str = "gpt-4-turbo"
    ):
        """
        Initialize Azure OpenAI client.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL (defaults to env var)
            api_key: Azure OpenAI API key (defaults to env var)
            api_version: API version to use
            default_deployment: Default deployment name to use
        """
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        
        if not self.azure_endpoint:
            raise ValueError("Azure OpenAI endpoint is required. Set AZURE_OPENAI_ENDPOINT environment variable.")
        if not self.api_key:
            raise ValueError("Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable.")
        
        self.api_version = api_version
        self.default_deployment = default_deployment
        
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
    
    def extract_structured_data(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Extract structured data using Azure OpenAI's JSON mode.
        
        Note: 'model' parameter is treated as deployment name in Azure.
        """
        try:
            deployment = model or self.default_deployment
            
            # Add schema to system message for guidance
            system_message = (
                "You are a data extraction assistant. Extract information according to the schema. "
                "Always respond with valid JSON matching the provided schema.\n\n"
                f"Schema:\n{json.dumps(schema, indent=2)}"
            )
            
            response = self.client.chat.completions.create(
                model=deployment,  # In Azure, this is the deployment name
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
            print(f"[Azure OpenAI] Tokens used: {usage.total_tokens} "
                  f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
            
            return result
            
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Azure OpenAI API: {e}")
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"Azure OpenAI rate limit exceeded: {e}")
        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise LLMError(f"Azure OpenAI API error: {e}")
    
    def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text completion using Azure OpenAI's Chat API.
        
        Note: 'model' parameter is treated as deployment name in Azure.
        """
        try:
            deployment = model or self.default_deployment
            
            kwargs = {
                "model": deployment,  # In Azure, this is the deployment name
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            
            response = self.client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Log token usage
            usage = response.usage
            print(f"[Azure OpenAI] Tokens used: {usage.total_tokens} "
                  f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
            
            return content
            
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"Failed to connect to Azure OpenAI API: {e}")
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"Azure OpenAI rate limit exceeded: {e}")
        except Exception as e:
            raise LLMError(f"Azure OpenAI API error: {e}")
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available deployment names.
        
        Note: In Azure, you work with deployments, not model names directly.
        Returns common deployment names as reference.
        """
        return [
            "gpt-4-turbo",
            "gpt-4",
            "gpt-35-turbo",
            "gpt-35-turbo-16k"
        ]
