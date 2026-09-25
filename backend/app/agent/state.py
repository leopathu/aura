from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    conversation_id: str
    user_id: str
    organization_id: str
    user_request: str

    intent: Optional[str] = None  # ASK, ANALYZE, RETRIEVE, ACT
    plan: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)

    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)

    retrieved_documents: List[Dict[str, Any]] = Field(default_factory=list)
    database_results: List[Dict[str, Any]] = Field(default_factory=list)
    intermediate_findings: List[str] = Field(default_factory=list)

    final_answer: str = ""
    reasoning_summary: str = ""
    citations: List[str] = Field(default_factory=list)
    report_artifact: Optional[Dict[str, Any]] = None
