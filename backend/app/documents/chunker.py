from typing import List, Dict, Any
from app.documents.parser import ParsedSection

class ChunkItem:
    def __init__(self, content: str, chunk_index: int, metadata: Dict[str, Any]):
        self.content = content
        self.chunk_index = chunk_index
        self.metadata = metadata

class TextChunker:
    @staticmethod
    def chunk_sections(
        sections: List[ParsedSection],
        chunk_size: int = 800,
        chunk_overlap: int = 100
    ) -> List[ChunkItem]:
        """
        Splits sections into chunks respecting boundaries and carrying forward metadata.
        """
        chunks: List[ChunkItem] = []
        global_index = 0

        for sec in sections:
            text = sec.content
            if len(text) <= chunk_size:
                chunks.append(
                    ChunkItem(
                        content=text,
                        chunk_index=global_index,
                        metadata={
                            "page": sec.page_number,
                            "section": sec.section_title
                        }
                    )
                )
                global_index += 1
                continue

            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                # Attempt to break at whitespace
                if end < len(text):
                    last_space = text.rfind(" ", start + chunk_size // 2, end)
                    if last_space != -1:
                        end = last_space

                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(
                        ChunkItem(
                            content=chunk_text,
                            chunk_index=global_index,
                            metadata={
                                "page": sec.page_number,
                                "section": sec.section_title
                            }
                        )
                    )
                    global_index += 1

                start = end - chunk_overlap if end < len(text) else len(text)

        return chunks
