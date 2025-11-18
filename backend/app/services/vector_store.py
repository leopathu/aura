from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any, Optional
from app.core.config import settings
import uuid


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
            api_key=settings.QDRANT_API_KEY,
            prefer_grpc=False
        )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
    
    def add_vectors(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        brain_id: int,
        document_id: int
    ) -> List[str]:
        """Add vectors to the collection."""
        points = []
        vector_ids = []
        
        for i, (vector, payload) in enumerate(zip(vectors, payloads)):
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            # Add brain_id and document_id to payload for filtering
            payload["brain_id"] = brain_id
            payload["document_id"] = document_id
            
            points.append(
                PointStruct(
                    id=vector_id,
                    vector=vector,
                    payload=payload
                )
            )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return vector_ids
    
    def search(
        self,
        query_vector: List[float],
        brain_id: int,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="brain_id",
                        match=MatchValue(value=brain_id)
                    )
                ]
            ),
            limit=limit,
            score_threshold=score_threshold
        )
        
        results = []
        for scored_point in search_result:
            results.append({
                "id": scored_point.id,
                "score": scored_point.score,
                "payload": scored_point.payload
            })
        
        return results
    
    def delete_by_document(self, document_id: int):
        """Delete all vectors for a document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
    
    def delete_by_brain(self, brain_id: int):
        """Delete all vectors for a brain."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="brain_id",
                        match=MatchValue(value=brain_id)
                    )
                ]
            )
        )


# Global instance
vector_store = VectorStore()
