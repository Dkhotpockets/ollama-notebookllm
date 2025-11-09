"""
Multi-Provider LLM Client for NotebookLlama
Enhanced from RAGFlow-Slim integration
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    """Standard response format for LLM operations"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingResponse:
    """Standard response format for embedding operations"""
    embedding: List[float]
    provider: str
    model: str
    dimensions: int
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None


class MultiLLMProvider:
    """Multi-provider LLM client with auto-detection and fallback"""
    
    def __init__(self, 
                 google_api_key: Optional[str] = None,
                 openai_api_key: Optional[str] = None,
                 anthropic_api_key: Optional[str] = None,
                 ollama_host: Optional[str] = None):
        
        # API keys from parameters or environment
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Provider clients (lazy loaded)
        self._openai_client = None
        self._google_client = None
        self._anthropic_client = None
        
        # Detection cache
        self._available_providers = None
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available LLM providers based on configuration"""
        if self._available_providers is None:
            providers = []
            
            # Check OpenAI
            if self.openai_api_key:
                providers.append(LLMProvider.OPENAI)
            
            # Check Google Gemini
            if self.google_api_key:
                providers.append(LLMProvider.GOOGLE_GEMINI)
            
            # Check Anthropic
            if self.anthropic_api_key:
                providers.append(LLMProvider.ANTHROPIC)
            
            # Check Ollama (always check since it's local)
            if self._is_ollama_available():
                providers.append(LLMProvider.OLLAMA)
            
            self._available_providers = providers
        
        return self._available_providers
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama is running locally"""
        try:
            import requests
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_primary_provider(self) -> Optional[LLMProvider]:
        """Get the primary (preferred) provider"""
        available = self.get_available_providers()
        
        if not available:
            return None
        
        # Priority order: Google Gemini > OpenAI > Anthropic > Ollama
        priority_order = [
            LLMProvider.GOOGLE_GEMINI,
            LLMProvider.OPENAI, 
            LLMProvider.ANTHROPIC,
            LLMProvider.OLLAMA
        ]
        
        for provider in priority_order:
            if provider in available:
                return provider
        
        return available[0]
    
    async def generate_completion(self, 
                                prompt: str,
                                provider: Optional[LLMProvider] = None,
                                model: Optional[str] = None,
                                max_tokens: int = 1000,
                                temperature: float = 0.7,
                                system_prompt: Optional[str] = None) -> LLMResponse:
        """Generate text completion using specified or auto-detected provider"""
        
        # Use specified provider or auto-detect
        target_provider = provider or self.get_primary_provider()
        
        if not target_provider:
            raise ValueError("No LLM providers available")
        
        try:
            if target_provider == LLMProvider.OPENAI:
                return await self._openai_completion(prompt, model, max_tokens, temperature, system_prompt)
            elif target_provider == LLMProvider.GOOGLE_GEMINI:
                return await self._google_completion(prompt, model, max_tokens, temperature, system_prompt)
            elif target_provider == LLMProvider.ANTHROPIC:
                return await self._anthropic_completion(prompt, model, max_tokens, temperature, system_prompt)
            elif target_provider == LLMProvider.OLLAMA:
                return await self._ollama_completion(prompt, model, max_tokens, temperature, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {target_provider}")
        
        except Exception as e:
            logger.error(f"Error with {target_provider.value}: {e}")
            
            # Try fallback providers
            available = self.get_available_providers()
            for fallback_provider in available:
                if fallback_provider != target_provider:
                    try:
                        logger.info(f"Trying fallback provider: {fallback_provider.value}")
                        return await self.generate_completion(
                            prompt, fallback_provider, model, max_tokens, temperature, system_prompt
                        )
                    except Exception as fallback_error:
                        logger.error(f"Fallback {fallback_provider.value} also failed: {fallback_error}")
                        continue
            
            # All providers failed
            raise Exception(f"All LLM providers failed. Last error: {e}")
    
    async def generate_embedding(self, 
                               text: str,
                               provider: Optional[LLMProvider] = None,
                               model: Optional[str] = None) -> EmbeddingResponse:
        """Generate text embedding using specified or auto-detected provider"""
        
        target_provider = provider or self.get_primary_provider()
        
        if not target_provider:
            raise ValueError("No embedding providers available")
        
        try:
            if target_provider == LLMProvider.OPENAI:
                return await self._openai_embedding(text, model)
            elif target_provider == LLMProvider.OLLAMA:
                return await self._ollama_embedding(text, model)
            else:
                # Fallback to OpenAI for embeddings if other providers don't support
                if LLMProvider.OPENAI in self.get_available_providers():
                    return await self._openai_embedding(text, model)
                elif LLMProvider.OLLAMA in self.get_available_providers():
                    return await self._ollama_embedding(text, model)
                else:
                    raise ValueError("No embedding providers available")
        
        except Exception as e:
            logger.error(f"Error generating embedding with {target_provider.value}: {e}")
            raise
    
    async def _openai_completion(self, prompt: str, model: Optional[str], max_tokens: int, 
                               temperature: float, system_prompt: Optional[str]) -> LLMResponse:
        """OpenAI completion implementation"""
        try:
            import openai
            from time import time
        except ImportError:
            raise ImportError("OpenAI package not installed: pip install openai")
        
        if not self._openai_client:
            self._openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        start_time = time()
        
        model = model or "gpt-4o-mini"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        processing_time = time() - start_time
        
        return LLMResponse(
            content=response.choices[0].message.content,
            provider="openai",
            model=model,
            tokens_used=response.usage.total_tokens,
            processing_time=processing_time
        )
    
    async def _google_completion(self, prompt: str, model: Optional[str], max_tokens: int,
                               temperature: float, system_prompt: Optional[str]) -> LLMResponse:
        """Google Gemini completion implementation"""
        try:
            from google import genai
            from time import time
        except ImportError:
            raise ImportError("Google GenAI package not installed: pip install google-genai")
        
        if not self._google_client:
            self._google_client = genai.Client(api_key=self.google_api_key)
        
        start_time = time()
        
        model = model or "gemini-1.5-flash"
        
        # Combine system prompt and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self._google_client.models.generate_content(
            model=f"models/{model}",
            contents=full_prompt,
            config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        
        processing_time = time() - start_time
        
        return LLMResponse(
            content=response.text,
            provider="google_gemini",
            model=model,
            processing_time=processing_time
        )
    
    async def _anthropic_completion(self, prompt: str, model: Optional[str], max_tokens: int,
                                  temperature: float, system_prompt: Optional[str]) -> LLMResponse:
        """Anthropic Claude completion implementation"""
        try:
            import anthropic
            from time import time
        except ImportError:
            raise ImportError("Anthropic package not installed: pip install anthropic")
        
        if not self._anthropic_client:
            self._anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        start_time = time()
        
        model = model or "claude-3-5-sonnet-20241022"
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self._anthropic_client.messages.create(**kwargs)
        
        processing_time = time() - start_time
        
        return LLMResponse(
            content=response.content[0].text,
            provider="anthropic",
            model=model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            processing_time=processing_time
        )
    
    async def _ollama_completion(self, prompt: str, model: Optional[str], max_tokens: int,
                               temperature: float, system_prompt: Optional[str]) -> LLMResponse:
        """Ollama completion implementation"""
        try:
            import aiohttp
            from time import time
        except ImportError:
            raise ImportError("aiohttp required for Ollama: pip install aiohttp")
        
        start_time = time()
        
        model = model or "llama3.1"
        
        # Combine prompts for Ollama
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                data = await response.json()
                processing_time = time() - start_time
                
                return LLMResponse(
                    content=data.get("response", ""),
                    provider="ollama",
                    model=model,
                    processing_time=processing_time
                )
    
    async def _openai_embedding(self, text: str, model: Optional[str]) -> EmbeddingResponse:
        """OpenAI embedding implementation"""
        try:
            import openai
            from time import time
        except ImportError:
            raise ImportError("OpenAI package not installed: pip install openai")
        
        if not self._openai_client:
            self._openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        start_time = time()
        
        model = model or "text-embedding-3-small"
        
        response = self._openai_client.embeddings.create(
            input=text,
            model=model
        )
        
        processing_time = time() - start_time
        
        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            provider="openai",
            model=model,
            dimensions=len(response.data[0].embedding),
            tokens_used=response.usage.total_tokens,
            processing_time=processing_time
        )
    
    async def _ollama_embedding(self, text: str, model: Optional[str]) -> EmbeddingResponse:
        """Ollama embedding implementation"""
        try:
            import aiohttp
            from time import time
        except ImportError:
            raise ImportError("aiohttp required for Ollama: pip install aiohttp")
        
        start_time = time()
        
        model = model or "nomic-embed-text"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ollama_host}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama embedding API error: {response.status}")
                
                data = await response.json()
                processing_time = time() - start_time
                
                embedding = data.get("embedding", [])
                
                return EmbeddingResponse(
                    embedding=embedding,
                    provider="ollama", 
                    model=model,
                    dimensions=len(embedding),
                    processing_time=processing_time
                )


# Global instance for easy access
_llm_provider = None


def get_llm_provider() -> MultiLLMProvider:
    """Get global LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = MultiLLMProvider()
    return _llm_provider


# Convenience functions
async def generate_text(prompt: str, 
                       provider: Optional[LLMProvider] = None,
                       max_tokens: int = 1000,
                       temperature: float = 0.7,
                       system_prompt: Optional[str] = None) -> str:
    """Convenience function for text generation"""
    llm = get_llm_provider()
    response = await llm.generate_completion(
        prompt=prompt,
        provider=provider,
        max_tokens=max_tokens,
        temperature=temperature,
        system_prompt=system_prompt
    )
    return response.content


async def generate_embedding_vector(text: str, 
                                  provider: Optional[LLMProvider] = None) -> List[float]:
    """Convenience function for embedding generation"""
    llm = get_llm_provider()
    response = await llm.generate_embedding(text=text, provider=provider)
    return response.embedding


def list_available_providers() -> List[str]:
    """List available LLM providers"""
    llm = get_llm_provider()
    return [provider.value for provider in llm.get_available_providers()]


async def test_provider(provider: LLMProvider) -> Dict[str, Any]:
    """Test a specific provider to ensure it's working"""
    llm = get_llm_provider()
    
    try:
        # Test completion
        completion_response = await llm.generate_completion(
            prompt="Hello, please respond with 'Test successful'",
            provider=provider,
            max_tokens=50
        )
        
        # Test embedding if supported
        embedding_response = None
        if provider in [LLMProvider.OPENAI, LLMProvider.OLLAMA]:
            try:
                embedding_response = await llm.generate_embedding(
                    text="Test embedding",
                    provider=provider
                )
            except:
                pass  # Embedding not supported or failed
        
        return {
            "provider": provider.value,
            "status": "success",
            "completion_works": True,
            "completion_response": completion_response.content,
            "embedding_works": embedding_response is not None,
            "embedding_dimensions": embedding_response.dimensions if embedding_response else None
        }
        
    except Exception as e:
        return {
            "provider": provider.value,
            "status": "failed",
            "error": str(e),
            "completion_works": False,
            "embedding_works": False
        }