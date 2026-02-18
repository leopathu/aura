"""
MCP Tools for LangGraph Integration
Wraps MCP server tools for use with LangChain/LangGraph agents
"""

from typing import Any, Dict, List, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, create_model
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.services.mcp_service import (
    get_mcp_client,
    get_mcp_registry,
    MCPErrorHandler
)


class UniversalMCPToolInput(BaseModel):
    """Dynamic input schema for MCP tools"""
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool arguments as key-value pairs"
    )


class UniversalMCPTool(BaseTool):
    """
    Universal wrapper for MCP server tools
    
    Dynamically wraps any MCP tool and makes it available to LangChain agents
    """
    name: str
    description: str
    server_name: str
    tool_name: str
    input_schema: Dict[str, Any]
    args_schema: Type[BaseModel] = UniversalMCPToolInput
    
    def __init__(
        self,
        server_name: str,
        tool_name: str,
        tool_description: str,
        input_schema: Dict[str, Any],
        **kwargs
    ):
        """
        Initialize universal MCP tool wrapper
        
        Args:
            server_name: MCP server name
            tool_name: Tool name on the server
            tool_description: Tool description
            input_schema: JSON schema for tool inputs
        """
        # Create a dynamic Pydantic model from the input schema
        dynamic_model = create_dynamic_model_from_schema(
            f"{tool_name}Input",
            input_schema
        )
        
        super().__init__(
            name=f"mcp_{server_name}_{tool_name}",
            description=tool_description,
            server_name=server_name,
            tool_name=tool_name,
            input_schema=input_schema,
            args_schema=dynamic_model,
            **kwargs
        )
    
    async def _arun(self, **kwargs) -> str:
        """Execute the MCP tool asynchronously"""
        try:
            client = get_mcp_client()
            
            # Call the MCP tool
            result = await client.call_tool(
                self.server_name,
                self.tool_name,
                kwargs
            )
            
            # Handle the result
            if result.get("success"):
                content = result.get("content", [])
                if isinstance(content, list):
                    return "\n".join(str(item) for item in content)
                return str(content)
            else:
                error_msg = result.get("error", "Unknown error")
                return f"❌ MCP Tool Error: {error_msg}"
        
        except Exception as e:
            error = MCPErrorHandler.handle_tool_call_error(
                self.server_name,
                self.tool_name,
                e
            )
            return f"❌ Failed to execute MCP tool: {error['message']}"
    
    def _run(self, **kwargs) -> str:
        """Sync version not implemented"""
        return "Use async version (_arun) instead"


def create_dynamic_model_from_schema(
    model_name: str,
    schema: Dict[str, Any]
) -> Type[BaseModel]:
    """
    Create a dynamic Pydantic model from JSON schema
    
    Args:
        model_name: Name for the model
        schema: JSON schema definition
        
    Returns:
        Pydantic model class
    """
    if not schema or "properties" not in schema:
        return UniversalMCPToolInput
    
    fields = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for field_name, field_schema in properties.items():
        field_type = get_python_type_from_json_schema(field_schema)
        field_description = field_schema.get("description", "")
        
        # Determine if field is required
        if field_name in required:
            fields[field_name] = (field_type, Field(description=field_description))
        else:
            fields[field_name] = (
                Optional[field_type],
                Field(default=None, description=field_description)
            )
    
    # If no fields, return default input model
    if not fields:
        return UniversalMCPToolInput
    
    # Create dynamic model
    try:
        return create_model(model_name, **fields)
    except Exception:
        # Fallback to universal input if model creation fails
        return UniversalMCPToolInput


def get_python_type_from_json_schema(schema: Dict[str, Any]) -> Type:
    """
    Convert JSON schema type to Python type
    
    Args:
        schema: JSON schema field definition
        
    Returns:
        Python type
    """
    json_type = schema.get("type", "string")
    
    type_mapping = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    
    return type_mapping.get(json_type, str)


class MCPToolRegistry:
    """
    Registry for managing MCP tools in LangGraph
    
    Handles dynamic tool loading and integration with agent workflows
    """
    
    def __init__(self):
        self._tools: Dict[str, UniversalMCPTool] = {}
    
    async def load_tools_from_server(self, server_name: str) -> List[BaseTool]:
        """
        Load all tools from an MCP server
        
        Args:
            server_name: Name of MCP server
            
        Returns:
            List of LangChain tools
        """
        tools = []
        
        try:
            client = get_mcp_client()
            mcp_tools = await client.list_tools(server_name)
            
            for tool_def in mcp_tools:
                tool = UniversalMCPTool(
                    server_name=server_name,
                    tool_name=tool_def["name"],
                    tool_description=tool_def["description"],
                    input_schema=tool_def["input_schema"]
                )
                
                # Store in registry
                tool_key = f"{server_name}_{tool_def['name']}"
                self._tools[tool_key] = tool
                tools.append(tool)
        
        except Exception as e:
            # Log error but don't fail - return empty list
            pass
        
        return tools
    
    async def load_all_mcp_tools(self) -> List[BaseTool]:
        """
        Load tools from all registered MCP servers
        
        Returns:
            List of all MCP tools
        """
        all_tools = []
        
        registry = get_mcp_registry()
        servers = registry.list_servers()
        
        for server in servers:
            server_tools = await self.load_tools_from_server(server["name"])
            all_tools.extend(server_tools)
        
        return all_tools
    
    def get_tool(self, server_name: str, tool_name: str) -> Optional[UniversalMCPTool]:
        """Get a specific tool from registry"""
        tool_key = f"{server_name}_{tool_name}"
        return self._tools.get(tool_key)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all loaded tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "server": tool.server_name,
                "tool_name": tool.tool_name
            }
            for tool in self._tools.values()
        ]


# Global MCP tool registry
_mcp_tool_registry = MCPToolRegistry()


def get_mcp_tool_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry"""
    return _mcp_tool_registry


async def get_mcp_tools(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    server_name: Optional[str] = None
) -> List[BaseTool]:
    """
    Get MCP tools for an agent
    
    Args:
        db: Database session (for consistency with other tools)
        user_id: User ID (for future permission checks)
        org_id: Organization ID (for multi-tenancy)
        server_name: Optional specific server to load from
        
    Returns:
        List of MCP tools
    """
    registry = get_mcp_tool_registry()
    
    if server_name:
        return await registry.load_tools_from_server(server_name)
    else:
        return await registry.load_all_mcp_tools()


async def refresh_mcp_tools():
    """
    Refresh all MCP tools from registered servers
    
    Useful for dynamic tool discovery and updates
    """
    registry = get_mcp_tool_registry()
    return await registry.load_all_mcp_tools()
