from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional

class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """Execute chat completion and return response text."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """Compute vector embeddings for a list of texts."""
        pass

    async def get_available_models(self) -> List[str]:
        """Fetch or list dynamically available models from provider."""
        return []

