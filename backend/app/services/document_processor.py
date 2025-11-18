import os
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
from PIL import Image
import pytesseract
from io import BytesIO
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store
import uuid


class DocumentProcessor:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
    
    async def save_file(self, file_content: bytes, filename: str, brain_id: int) -> str:
        """Save uploaded file to disk."""
        brain_dir = self.upload_dir / str(brain_id)
        brain_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = brain_dir / unique_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        return str(file_path)
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from PDF file."""
        chunks = []
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    chunks.append({
                        "content": text,
                        "page": page_num + 1,
                        "type": "pdf"
                    })
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
        
        return chunks
    
    def extract_text_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from DOCX file."""
        chunks = []
        try:
            doc = DocxDocument(file_path)
            full_text = []
            
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # Combine paragraphs and split into chunks
            text = "\n".join(full_text)
            if text.strip():
                chunks.append({
                    "content": text,
                    "type": "docx"
                })
        except Exception as e:
            raise Exception(f"Error extracting text from DOCX: {str(e)}")
        
        return chunks
    
    def extract_text_from_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from TXT file."""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                if text.strip():
                    chunks.append({
                        "content": text,
                        "type": "txt"
                    })
        except Exception as e:
            raise Exception(f"Error extracting text from TXT: {str(e)}")
        
        return chunks
    
    def extract_text_from_image(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract text from image using OCR."""
        chunks = []
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            if text.strip():
                chunks.append({
                    "content": text,
                    "type": "image"
                })
        except Exception as e:
            raise Exception(f"Error extracting text from image: {str(e)}")
        
        return chunks
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence or word boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                last_space = chunk.rfind(' ')
                
                break_point = max(last_period, last_newline, last_space)
                if break_point > 0:
                    chunk = chunk[:break_point + 1]
                    end = start + len(chunk)
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    async def process_document(
        self,
        file_path: str,
        file_type: str,
        brain_id: int,
        document_id: int,
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """Process document and store in vector database."""
        # Extract text based on file type
        if file_type == "pdf":
            text_chunks = self.extract_text_from_pdf(file_path)
        elif file_type in ["docx", "doc"]:
            text_chunks = self.extract_text_from_docx(file_path)
        elif file_type == "txt":
            text_chunks = self.extract_text_from_txt(file_path)
        elif file_type in ["png", "jpg", "jpeg"]:
            text_chunks = self.extract_text_from_image(file_path)
        else:
            raise Exception(f"Unsupported file type: {file_type}")
        
        # Process each chunk
        all_vectors = []
        all_payloads = []
        
        for chunk_data in text_chunks:
            content = chunk_data["content"]
            
            # Further split large chunks
            sub_chunks = self.chunk_text(content)
            
            for sub_chunk in sub_chunks:
                # Create embedding
                embedding = await embedding_service.create_embedding(sub_chunk)
                
                # Prepare payload
                payload = {
                    "content": sub_chunk,
                    "document_id": document_id,
                    "brain_id": brain_id,
                    "file_type": file_type,
                    **(metadata or {}),
                    **{k: v for k, v in chunk_data.items() if k != "content"}
                }
                
                all_vectors.append(embedding)
                all_payloads.append(payload)
        
        # Store in vector database
        vector_ids = vector_store.add_vectors(
            vectors=all_vectors,
            payloads=all_payloads,
            brain_id=brain_id,
            document_id=document_id
        )
        
        return vector_ids
    
    async def delete_file(self, file_path: str):
        """Delete file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {str(e)}")


# Global instance
document_processor = DocumentProcessor()
