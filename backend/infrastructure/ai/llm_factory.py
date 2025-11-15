"""
LLM Factory

Factory for creating appropriate LLM client based on environment configuration.
Supports automatic provider selection: Azure OpenAI > Anthropic > OpenAI > Ollama.
"""

import os
from typing import Optional

from domain.repositories.llm_client import ILLMClient


class LLMFactory:
    """
    Factory for creating LLM client instances based on environment configuration.
    
    Checks environment variables in priority order and returns the first available client:
    1. Azure OpenAI (AZURE_OPENAI_ENDPOINT)
    2. Anthropic Claude (ANTHROPIC_API_KEY) - Future implementation
    3. OpenAI (OPENAI_API_KEY)
    4. Ollama (OLLAMA_HOST) - Future implementation
    """
    
    @staticmethod
    def create_client() -> ILLMClient:
        """
        Create an LLM client based on available environment configuration.
        
        Returns:
            Configured ILLMClient instance
            
        Raises:
            ValueError: If no valid LLM configuration is found
        """
        # Try Azure OpenAI first
        if os.getenv("AZURE_OPENAI_ENDPOINT"):
            from infrastructure.ai.azure_openai_client import AzureOpenAIClient
            return AzureOpenAIClient()
        
        # Try standard OpenAI
        if os.getenv("OPENAI_API_KEY"):
            from infrastructure.ai.openai_client import OpenAIClient
            return OpenAIClient()
        
        # Future: Add Anthropic support
        # if os.getenv("ANTHROPIC_API_KEY"):
        #     from infrastructure.ai.anthropic_client import AnthropicClient
        #     return AnthropicClient()
        
        # Future: Add Ollama support
        # if os.getenv("OLLAMA_HOST"):
        #     from infrastructure.ai.ollama_client import OllamaClient
        #     return OllamaClient()
        
        raise ValueError(
            "No LLM provider configured. Please set one of the following environment variables:\n"
            "  - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY (for Azure OpenAI)\n"
            "  - OPENAI_API_KEY (for OpenAI)\n"
            "  - ANTHROPIC_API_KEY (for Anthropic Claude - coming soon)\n"
            "  - OLLAMA_HOST (for local Ollama - coming soon)"
        )
    
    @staticmethod
    def create_openai_client(
        api_key: Optional[str] = None,
        default_model: str = "gpt-4-turbo-preview"
    ) -> ILLMClient:
        """
        Create an OpenAI client explicitly.
        
        Args:
            api_key: Optional API key (uses env var if not provided)
            default_model: Default model to use
            
        Returns:
            OpenAI client instance
        """
        from infrastructure.ai.openai_client import OpenAIClient
        return OpenAIClient(api_key=api_key, default_model=default_model)
    
    @staticmethod
    def create_azure_openai_client(
        azure_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
        default_deployment: str = "gpt-4-turbo"
    ) -> ILLMClient:
        """
        Create an Azure OpenAI client explicitly.
        
        Args:
            azure_endpoint: Azure endpoint URL
            api_key: Azure API key
            api_version: API version
            default_deployment: Default deployment name
            
        Returns:
            Azure OpenAI client instance
        """
        from infrastructure.ai.azure_openai_client import AzureOpenAIClient
        return AzureOpenAIClient(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            default_deployment=default_deployment
        )
