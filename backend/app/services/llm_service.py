from openai import AsyncOpenAI
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS
    
    async def generate_response(
        self,
        query: str,
        brain_id: int,
        chat_history: List[Dict[str, str]] = None,
        max_context_docs: int = 5
    ) -> Dict[str, Any]:
        """Generate response using RAG."""
        # Create embedding for query
        query_embedding = await embedding_service.create_embedding(query)
        
        # Search for relevant documents
        search_results = vector_store.search(
            query_vector=query_embedding,
            brain_id=brain_id,
            limit=max_context_docs,
            score_threshold=0.7
        )
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            payload = result["payload"]
            context_parts.append(payload["content"])
            sources.append({
                "document_id": payload["document_id"],
                "content": payload["content"][:200] + "...",  # Preview
                "score": result["score"],
                "page": payload.get("page"),
                "file_type": payload.get("file_type")
            })
        
        context = "\n\n".join(context_parts)
        
        # Build messages for LLM
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant that answers questions based on the provided context. "
                    "Always base your answers on the context provided. If the context doesn't contain "
                    "relevant information, politely say so. Be concise and accurate."
                )
            }
        ]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history[-10:])  # Last 10 messages
        
        # Add current query with context
        user_message = f"Context:\n{context}\n\nQuestion: {query}"
        messages.append({"role": "user", "content": user_message})
        
        # Generate response
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(search_results) > 0
        }
    
    async def generate_chat_title(self, first_message: str) -> str:
        """Generate a title for a chat session based on the first message."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a short, concise title (max 6 words) for this conversation based on the user's message."
                    },
                    {
                        "role": "user",
                        "content": first_message
                    }
                ],
                temperature=0.7,
                max_tokens=20
            )
            title = response.choices[0].message.content.strip()
            return title
        except:
            return "New Chat"


# Global instance
llm_service = LLMService()
