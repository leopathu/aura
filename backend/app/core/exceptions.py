"""Custom application exception classes."""

from fastapi import HTTPException, status


class AuraException(Exception):
    """Base exception for the Aura application."""

    def __init__(self, detail: str, code: str = "INTERNAL_ERROR") -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)


class NotFoundException(AuraException):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, code="NOT_FOUND")


class EmbeddingException(AuraException):
    """Raised when embedding generation fails."""

    def __init__(self, detail: str = "Embedding generation failed") -> None:
        super().__init__(detail=detail, code="EMBEDDING_ERROR")


class LLMException(AuraException):
    """Raised when an LLM call fails."""

    def __init__(self, detail: str = "LLM generation failed") -> None:
        super().__init__(detail=detail, code="LLM_ERROR")


class DocumentIngestionException(AuraException):
    """Raised when document ingestion fails."""

    def __init__(self, detail: str = "Document ingestion failed") -> None:
        super().__init__(detail=detail, code="INGESTION_ERROR")
