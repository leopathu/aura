from openai import AsyncOpenAI
from typing import List
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
    
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts."""
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        embeddings = [item.embedding for item in response.data]
        return embeddings
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text."""
        embeddings = await self.create_embeddings([text])
        return embeddings[0]


# Global instance
embedding_service = EmbeddingService()
