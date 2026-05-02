"""Embedding service — generates vector embeddings via configurable providers."""

from __future__ import annotations

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.exceptions import EmbeddingException


def _build_embedding_client(
    provider: str, api_key: str, base_url: str
) -> openai.AsyncOpenAI:
    """Build an AsyncOpenAI client for the given embedding provider."""
    if provider == "ollama":
        resolved = (base_url.rstrip("/") + "/v1") if base_url else "http://host.docker.internal:11434/v1"
        return openai.AsyncOpenAI(api_key="ollama", base_url=resolved)
    if provider == "google":
        return openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    # Default: openai
    return openai.AsyncOpenAI(api_key=api_key)


class EmbeddingService:
    """Generates text embeddings using the configured provider/model."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model or settings.embedding_model
        self._client = _build_embedding_client(
            provider or "openai",
            api_key or settings.openai_api_key,
            base_url or "http://localhost:11434",
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=text,
            )
            return response.data[0].embedding
        except openai.OpenAIError as exc:
            raise EmbeddingException(f"Embedding error: {exc}") from exc

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
            )
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        except openai.OpenAIError as exc:
            raise EmbeddingException(f"Embedding batch error: {exc}") from exc


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
