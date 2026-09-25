import os
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Document, DocumentChunk, AIProvider, AIModel
from app.documents.parser import DocumentParser
from app.documents.chunker import TextChunker
from app.models_ai.factory import get_llm_provider
from app.models_ai.providers import MockAIProvider

class IngestionService:
    @staticmethod
    async def process_document(db: AsyncSession, document_id: str) -> None:
        """Parses, chunks, embeds, and indexes an uploaded document."""
        doc_res = await db.execute(select(Document).where(Document.id == document_id))
        doc = doc_res.scalar_one_or_none()
        if not doc:
            return

        try:
            # 1. Parse
            sections = DocumentParser.parse_file(doc.storage_path, doc.file_type)
            if not sections:
                doc.status = "INDEXED"
                doc.chunk_count = 0
                await db.commit()
                return

            # 2. Chunk
            chunks = TextChunker.chunk_sections(sections, chunk_size=800, chunk_overlap=100)

            # 3. Embed
            # Fetch active embedding model if configured
            prov_stmt = select(AIProvider).where(
                AIProvider.organization_id == doc.organization_id,
                AIProvider.is_active == True
            )
            prov_res = await db.execute(prov_stmt)
            provider_record = prov_res.scalar_one_or_none()

            llm_provider = get_llm_provider(provider_record) if provider_record else MockAIProvider()

            texts_to_embed = [c.content for c in chunks]
            embeddings = await llm_provider.embed(texts_to_embed)

            # 4. Save chunks
            for i, chunk_item in enumerate(chunks):
                vec = embeddings[i] if i < len(embeddings) else None
                chunk_obj = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_item.chunk_index,
                    content=chunk_item.content,
                    metadata_json=chunk_item.metadata,
                    embedding_vector=vec
                )
                db.add(chunk_obj)

            doc.chunk_count = len(chunks)
            doc.status = "INDEXED"
            await db.commit()

        except Exception as e:
            await db.rollback()
            doc.status = "FAILED"
            doc.error_message = str(e)
            await db.commit()
            raise e
