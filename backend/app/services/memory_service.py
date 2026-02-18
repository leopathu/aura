"""
Agent Memory Service

Provides semantic memory functionality using vector embeddings.

TASK-300: Generate embeddings for memory content
TASK-301: Store memory with embeddings
TASK-302: Semantic search using pgvector
TASK-303: Retrieve relevant memories for context
TASK-304: Memory summarization
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.models.agent import AgentMemory, Agent
from app.services.llm_service import get_llm_client


# ===== EMBEDDING GENERATION (TASK-300) =====

async def generate_embedding(
    content: str,
    model: str = "text-embedding-3-small"
) -> List[float]:
    """
    Generate embedding vector for content using OpenAI
    
    TASK-300: Generate embeddings
    
    Args:
        content: Text content to embed
        model: OpenAI embedding model (default: text-embedding-3-small)
    
    Returns:
        List of floats representing the embedding vector (1536 dimensions)
    """
    try:
        from openai import AsyncOpenAI
        import os
        
        # Get OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Generate embedding
        response = await client.embeddings.create(
            model=model,
            input=content
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        print(f"Error generating embedding: {e}")
        raise


async def generate_embeddings_batch(
    contents: List[str],
    model: str = "text-embedding-3-small"
) -> List[List[float]]:
    """
    Generate embeddings for multiple contents in batch
    
    More efficient than individual calls for large datasets
    """
    try:
        from openai import AsyncOpenAI
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        client = AsyncOpenAI(api_key=api_key)
        
        # Batch generation (OpenAI supports up to 2048 inputs)
        response = await client.embeddings.create(
            model=model,
            input=contents
        )
        
        return [item.embedding for item in response.data]
        
    except Exception as e:
        print(f"Error generating batch embeddings: {e}")
        raise


# ===== MEMORY STORAGE (TASK-301) =====

async def store_memory(
    db: Session,
    agent_id: UUID,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    auto_embed: bool = True
) -> AgentMemory:
    """
    Store a memory with optional automatic embedding generation
    
    TASK-301: Store memory with embeddings
    
    Args:
        db: Database session
        agent_id: Agent ID
        content: Memory content
        metadata: Optional metadata dictionary
        auto_embed: If True, automatically generate embedding
    
    Returns:
        Created AgentMemory instance
    """
    # Generate embedding if requested
    embedding = None
    if auto_embed:
        embedding = await generate_embedding(content)
    
    # Create memory
    memory = AgentMemory(
        agent_id=agent_id,
        content=content,
        embedding=embedding,
        memory_metadata=metadata or {}
    )
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    
    return memory


async def store_memory_with_embedding(
    db: Session,
    agent_id: UUID,
    content: str,
    embedding: List[float],
    metadata: Optional[Dict[str, Any]] = None
) -> AgentMemory:
    """Store memory with pre-generated embedding"""
    memory = AgentMemory(
        agent_id=agent_id,
        content=content,
        embedding=embedding,
        memory_metadata=metadata or {}
    )
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    
    return memory


async def store_memories_batch(
    db: Session,
    agent_id: UUID,
    memories: List[Dict[str, Any]],
    auto_embed: bool = True
) -> List[AgentMemory]:
    """
    Store multiple memories in batch
    
    Args:
        db: Database session
        agent_id: Agent ID
        memories: List of dicts with 'content' and optional 'metadata'
        auto_embed: Generate embeddings in batch
    
    Returns:
        List of created AgentMemory instances
    """
    # Generate embeddings in batch if requested
    embeddings = []
    if auto_embed:
        contents = [m["content"] for m in memories]
        embeddings = await generate_embeddings_batch(contents)
    
    # Create memory objects
    memory_objects = []
    for i, memory_data in enumerate(memories):
        memory = AgentMemory(
            agent_id=agent_id,
            content=memory_data["content"],
            embedding=embeddings[i] if auto_embed else None,
            memory_metadata=memory_data.get("metadata", {})
        )
        memory_objects.append(memory)
    
    db.add_all(memory_objects)
    db.commit()
    
    for memory in memory_objects:
        db.refresh(memory)
    
    return memory_objects


# ===== SEMANTIC SEARCH (TASK-302) =====

async def semantic_search(
    db: Session,
    agent_id: UUID,
    query: str,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Search memories using semantic similarity
    
    TASK-302: Semantic search using pgvector
    
    Args:
        db: Database session
        agent_id: Agent ID
        query: Search query text
        limit: Maximum number of results
        similarity_threshold: Minimum similarity score (0-1)
    
    Returns:
        List of dicts with memory and similarity score
    """
    # Generate query embedding
    query_embedding = await generate_embedding(query)
    
    # Use pgvector cosine similarity
    # Convert embedding to PostgreSQL array format
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    # Raw SQL query using pgvector <=> operator (cosine distance)
    # Lower distance = higher similarity
    sql = text("""
        SELECT 
            id,
            agent_id,
            content,
            memory_metadata,
            created_at,
            1 - (embedding <=> :query_embedding::vector) as similarity
        FROM agent_memory
        WHERE agent_id = :agent_id
        AND embedding IS NOT NULL
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    result = db.execute(
        sql,
        {
            "query_embedding": embedding_str,
            "agent_id": str(agent_id),
            "limit": limit
        }
    )
    
    memories = []
    for row in result:
        similarity = row.similarity
        
        # Filter by similarity threshold
        if similarity >= similarity_threshold:
            memories.append({
                "id": row.id,
                "agent_id": row.agent_id,
                "content": row.content,
                "metadata": row.memory_metadata,
                "created_at": row.created_at,
                "similarity": similarity
            })
    
    return memories


async def find_similar_memories(
    db: Session,
    agent_id: UUID,
    content: str,
    limit: int = 5,
    exclude_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Find memories similar to given content
    
    Useful for deduplication or finding related memories
    """
    # Generate embedding for content
    embedding = await generate_embedding(content)
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    
    # Query with optional exclusion
    sql_parts = ["""
        SELECT 
            id,
            agent_id,
            content,
            memory_metadata,
            created_at,
            1 - (embedding <=> :query_embedding::vector) as similarity
        FROM agent_memory
        WHERE agent_id = :agent_id
        AND embedding IS NOT NULL
    """]
    
    params = {
        "query_embedding": embedding_str,
        "agent_id": str(agent_id),
        "limit": limit
    }
    
    if exclude_id:
        sql_parts.append("AND id != :exclude_id")
        params["exclude_id"] = str(exclude_id)
    
    sql_parts.append("""
        ORDER BY embedding <=> :query_embedding::vector
        LIMIT :limit
    """)
    
    sql = text("\n".join(sql_parts))
    result = db.execute(sql, params)
    
    memories = []
    for row in result:
        memories.append({
            "id": row.id,
            "agent_id": row.agent_id,
            "content": row.content,
            "metadata": row.memory_metadata,
            "created_at": row.created_at,
            "similarity": row.similarity
        })
    
    return memories


# ===== MEMORY RETRIEVAL (TASK-303) =====

async def retrieve_relevant_memories(
    db: Session,
    agent_id: UUID,
    context: str,
    max_memories: int = 5,
    similarity_threshold: float = 0.7
) -> List[str]:
    """
    Retrieve relevant memories for agent context
    
    TASK-303: Retrieve relevant memories
    
    Args:
        db: Database session
        agent_id: Agent ID
        context: Current conversation context
        max_memories: Maximum memories to retrieve
        similarity_threshold: Minimum similarity
    
    Returns:
        List of memory content strings
    """
    memories = await semantic_search(
        db=db,
        agent_id=agent_id,
        query=context,
        limit=max_memories,
        similarity_threshold=similarity_threshold
    )
    
    return [m["content"] for m in memories]


async def get_recent_memories(
    db: Session,
    agent_id: UUID,
    limit: int = 10,
    hours: Optional[int] = None
) -> List[AgentMemory]:
    """Get recent memories by time"""
    query = db.query(AgentMemory).filter(AgentMemory.agent_id == agent_id)
    
    if hours:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(AgentMemory.created_at >= cutoff)
    
    query = query.order_by(AgentMemory.created_at.desc()).limit(limit)
    
    return query.all()


async def get_memory_by_id(
    db: Session,
    memory_id: UUID,
    agent_id: UUID
) -> Optional[AgentMemory]:
    """Get specific memory by ID"""
    return db.query(AgentMemory).filter(
        AgentMemory.id == memory_id,
        AgentMemory.agent_id == agent_id
    ).first()


async def count_agent_memories(db: Session, agent_id: UUID) -> int:
    """Count total memories for agent"""
    return db.query(AgentMemory).filter(
        AgentMemory.agent_id == agent_id
    ).count()


# ===== MEMORY SUMMARIZATION (TASK-304) =====

async def summarize_memories(
    db: Session,
    agent_id: UUID,
    memories: List[str],
    llm_provider: str = "openai",
    model: str = "gpt-4o-mini"
) -> str:
    """
    Summarize multiple memories into condensed format
    
    TASK-304: Memory summarization
    
    Args:
        db: Database session
        agent_id: Agent ID
        memories: List of memory content strings
        llm_provider: LLM provider (openai, anthropic, google)
        model: Model name
    
    Returns:
        Summarized memory content
    """
    if not memories:
        return ""
    
    # Get LLM client
    from app.models.organization import Organization
    from app.models.agent import Agent
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError("Agent not found")
    
    # Build summarization prompt
    memories_text = "\n\n".join([f"Memory {i+1}: {m}" for i, m in enumerate(memories)])
    
    prompt = f"""You are summarizing past memories for an AI agent. Create a concise summary that captures the key information from these memories.

Memories to summarize:
{memories_text}

Provide a clear, structured summary that preserves important details while being concise."""
    
    try:
        # Get LLM client (this will use the agent's configured credentials)
        llm = await get_llm_client(
            db=db,
            org_id=agent.org_id,
            provider=llm_provider,
            model=model
        )
        
        # Generate summary
        response = await llm.ainvoke(prompt)
        
        # Extract content based on provider
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
            
    except Exception as e:
        print(f"Error summarizing memories: {e}")
        # Fallback: just concatenate
        return " ".join(memories[:3])  # Take first 3 memories


async def condense_old_memories(
    db: Session,
    agent_id: UUID,
    days_old: int = 30,
    keep_count: int = 10
) -> Optional[AgentMemory]:
    """
    Condense old memories into a summary
    
    Useful for maintaining manageable memory size while preserving context
    
    Args:
        db: Database session
        agent_id: Agent ID
        days_old: Memories older than this will be condensed
        keep_count: Keep this many recent memories unconsolidated
    
    Returns:
        Created summary memory or None
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    # Get old memories
    old_memories = db.query(AgentMemory).filter(
        AgentMemory.agent_id == agent_id,
        AgentMemory.created_at < cutoff_date
    ).order_by(AgentMemory.created_at.asc()).all()
    
    if len(old_memories) <= keep_count:
        return None  # Not enough memories to condense
    
    # Take all but the most recent keep_count
    memories_to_condense = old_memories[:-keep_count] if keep_count > 0 else old_memories
    
    if not memories_to_condense:
        return None
    
    # Extract content
    contents = [m.content for m in memories_to_condense]
    
    # Generate summary
    summary_content = await summarize_memories(
        db=db,
        agent_id=agent_id,
        memories=contents
    )
    
    # Store summary as new memory
    summary_memory = await store_memory(
        db=db,
        agent_id=agent_id,
        content=summary_content,
        metadata={
            "type": "summary",
            "condensed_count": len(memories_to_condense),
            "date_range": {
                "start": memories_to_condense[0].created_at.isoformat(),
                "end": memories_to_condense[-1].created_at.isoformat()
            }
        }
    )
    
    # Delete old memories that were condensed
    for memory in memories_to_condense:
        db.delete(memory)
    
    db.commit()
    
    return summary_memory


# ===== MEMORY MANAGEMENT =====

async def delete_memory(
    db: Session,
    memory_id: UUID,
    agent_id: UUID
) -> bool:
    """Delete a specific memory"""
    memory = db.query(AgentMemory).filter(
        AgentMemory.id == memory_id,
        AgentMemory.agent_id == agent_id
    ).first()
    
    if not memory:
        return False
    
    db.delete(memory)
    db.commit()
    return True


async def delete_agent_memories(
    db: Session,
    agent_id: UUID,
    older_than_days: Optional[int] = None
) -> int:
    """
    Delete all memories for an agent
    
    Args:
        db: Database session
        agent_id: Agent ID
        older_than_days: Only delete memories older than this
    
    Returns:
        Number of deleted memories
    """
    query = db.query(AgentMemory).filter(AgentMemory.agent_id == agent_id)
    
    if older_than_days:
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        query = query.filter(AgentMemory.created_at < cutoff)
    
    count = query.count()
    query.delete(synchronize_session=False)
    db.commit()
    
    return count


# ===== CONTEXT INJECTION =====

async def inject_memories_into_context(
    db: Session,
    agent_id: UUID,
    current_context: str,
    max_memories: int = 5
) -> str:
    """
    Retrieve relevant memories and inject them into agent context
    
    Args:
        db: Database session
        agent_id: Agent ID
        current_context: Current conversation/task context
        max_memories: Maximum memories to inject
    
    Returns:
        Enhanced context with memories
    """
    # Retrieve relevant memories
    memory_contents = await retrieve_relevant_memories(
        db=db,
        agent_id=agent_id,
        context=current_context,
        max_memories=max_memories
    )
    
    if not memory_contents:
        return current_context
    
    # Format memories
    memories_text = "\n".join([f"- {m}" for m in memory_contents])
    
    # Inject into context
    enhanced_context = f"""Relevant past memories:
{memories_text}

Current context:
{current_context}"""
    
    return enhanced_context


# Export all functions
__all__ = [
    "generate_embedding",
    "generate_embeddings_batch",
    "store_memory",
    "store_memory_with_embedding",
    "store_memories_batch",
    "semantic_search",
    "find_similar_memories",
    "retrieve_relevant_memories",
    "get_recent_memories",
    "get_memory_by_id",
    "count_agent_memories",
    "summarize_memories",
    "condense_old_memories",
    "delete_memory",
    "delete_agent_memories",
    "inject_memories_into_context"
]
