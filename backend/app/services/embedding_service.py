"""Embedding service — generates vector embeddings via OpenAI."""

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import EmbeddingException


class EmbeddingService:
    """Generates text embeddings using the configured OpenAI model."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Args:
            text: The input text to embed.

        Returns:
            A list of floats representing the embedding vector.

        Raises:
            EmbeddingException: If the API call fails after retries.
        """
        try:
            response = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=text,
            )
            return response.data[0].embedding
        except openai.OpenAIError as exc:
            raise EmbeddingException(f"OpenAI embedding error: {exc}") from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of input texts.

        Returns:
            List of embedding vectors in the same order as the input.

        Raises:
            EmbeddingException: If the API call fails after retries.
        """
        try:
            response = await self._client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
            )
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        except openai.OpenAIError as exc:
            raise EmbeddingException(f"OpenAI batch embedding error: {exc}") from exc
