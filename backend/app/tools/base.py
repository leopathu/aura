from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    required_permissions: List[str]
    resource_type: str  # DATABASE, DOCUMENT, CSV, MCP, REPORT, WEB

class ToolResultContainer:
    def __init__(
        self,
        success: bool,
        data: Any,
        error: Optional[str] = None,
        citations: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.citations = citations or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "citations": self.citations,
            "metadata": self.metadata,
        }

class BaseTool(ABC):
    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(
        self,
        context: Dict[str, Any],
        **kwargs: Any
    ) -> ToolResultContainer:
        pass
