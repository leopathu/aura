"""
MCP (Model Context Protocol) API Endpoints
Handles MCP server management and tool discovery
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.mcp_service import (
    get_mcp_registry,
    get_mcp_client,
    register_mcp_server,
    list_mcp_servers,
    list_mcp_tools,
    call_mcp_tool,
    discover_all_mcp_tools,
    MCPErrorHandler
)
from app.tools.mcp_tools import get_mcp_tool_registry, refresh_mcp_tools


router = APIRouter(prefix="/mcp", tags=["mcp"])


# ===== REQUEST/RESPONSE SCHEMAS =====

class MCPServerCreate(BaseModel):
    """Schema for creating/registering an MCP server"""
    name: str = Field(description="Unique server identifier")
    command: str = Field(description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    description: str = Field(default="", description="Server description")


class MCPServerResponse(BaseModel):
    """Schema for MCP server information"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    description: str


class MCPToolSchema(BaseModel):
    """Schema for MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server: str


class MCPToolCall(BaseModel):
    """Schema for calling an MCP tool"""
    server_name: str = Field(description="MCP server name")
    tool_name: str = Field(description="Tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPToolCallResponse(BaseModel):
    """Schema for MCP tool call result"""
    success: bool
    content: List[Any] = Field(default_factory=list)
    error: Optional[str] = None
    isError: bool = False


# ===== MCP SERVER MANAGEMENT ENDPOINTS =====

@router.post("/servers", status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_data: MCPServerCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Register a new MCP server
    
    Adds an MCP server to the registry for tool discovery
    """
    try:
        success = await register_mcp_server(
            name=server_data.name,
            command=server_data.command,
            args=server_data.args,
            env=server_data.env,
            description=server_data.description
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register MCP server"
            )
        
        return {
            "message": f"MCP server '{server_data.name}' registered successfully",
            "server": server_data.dict()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register server: {str(e)}"
        )


@router.get("/servers", response_model=List[MCPServerResponse])
async def get_mcp_servers(
    current_user: User = Depends(get_current_user)
):
    """
    List all registered MCP servers
    """
    try:
        servers = await list_mcp_servers()
        return servers
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        )


@router.delete("/servers/{server_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Unregister an MCP server
    """
    try:
        registry = get_mcp_registry()
        registry.unregister_server(server_name)
        return None
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete server: {str(e)}"
        )


# ===== MCP TOOL DISCOVERY ENDPOINTS =====

@router.get("/servers/{server_name}/tools", response_model=List[MCPToolSchema])
async def get_server_tools(
    server_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    List all tools available from a specific MCP server
    """
    try:
        tools = await list_mcp_tools(server_name)
        return tools
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/tools/discover")
async def discover_tools(
    current_user: User = Depends(get_current_user)
):
    """
    Discover tools from all registered MCP servers
    """
    try:
        all_tools = await discover_all_mcp_tools()
        return all_tools
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover tools: {str(e)}"
        )


@router.post("/tools/refresh")
async def refresh_tools(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh MCP tools for agent use
    
    Re-discovers and loads all tools from registered servers
    """
    try:
        tools = await refresh_mcp_tools()
        return {
            "message": "MCP tools refreshed successfully",
            "tool_count": len(tools)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tools: {str(e)}"
        )


# ===== MCP TOOL EXECUTION ENDPOINTS =====

@router.post("/tools/call", response_model=MCPToolCallResponse)
async def call_tool(
    tool_call: MCPToolCall,
    current_user: User = Depends(get_current_user)
):
    """
    Call an MCP tool directly
    
    Useful for testing and debugging MCP integrations
    """
    try:
        result = await call_mcp_tool(
            server_name=tool_call.server_name,
            tool_name=tool_call.tool_name,
            arguments=tool_call.arguments
        )
        
        return result
    
    except Exception as e:
        error = MCPErrorHandler.handle_tool_call_error(
            tool_call.server_name,
            tool_call.tool_name,
            e
        )
        return {
            "success": False,
            "content": [],
            "error": error["message"],
            "isError": True
        }


@router.get("/tools/registry")
async def get_tool_registry(
    current_user: User = Depends(get_current_user)
):
    """
    Get all tools loaded in the MCP tool registry
    
    Shows tools currently available to agents
    """
    try:
        registry = get_mcp_tool_registry()
        tools = registry.list_tools()
        return {
            "tool_count": len(tools),
            "tools": tools
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool registry: {str(e)}"
        )


# ===== HEALTH CHECK =====

@router.get("/health")
async def mcp_health_check():
    """
    Check MCP service health
    """
    try:
        registry = get_mcp_registry()
        servers = registry.list_servers()
        
        return {
            "status": "healthy",
            "server_count": len(servers),
            "servers": [s["name"] for s in servers]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MCP service unhealthy: {str(e)}"
        )
