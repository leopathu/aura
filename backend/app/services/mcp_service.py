"""
Model Context Protocol (MCP) Service
Handles MCP server connections and tool discovery
"""

from typing import Dict, List, Any, Optional
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import asynccontextmanager


class MCPServerRegistry:
    """
    Registry for MCP servers
    
    Maintains a list of available MCP servers and their configurations
    """
    
    def __init__(self):
        self._servers: Dict[str, Dict[str, Any]] = {}
    
    def register_server(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        description: str = ""
    ):
        """
        Register an MCP server
        
        Args:
            name: Unique server name/identifier
            command: Command to start the server
            args: Command arguments
            env: Environment variables
            description: Human-readable description
        """
        self._servers[name] = {
            "name": name,
            "command": command,
            "args": args or [],
            "env": env or {},
            "description": description
        }
    
    def unregister_server(self, name: str):
        """Remove a server from registry"""
        if name in self._servers:
            del self._servers[name]
    
    def get_server(self, name: str) -> Optional[Dict[str, Any]]:
        """Get server configuration by name"""
        return self._servers.get(name)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers"""
        return list(self._servers.values())
    
    def get_server_params(self, name: str) -> Optional[StdioServerParameters]:
        """
        Get StdioServerParameters for a server
        
        Args:
            name: Server name
            
        Returns:
            StdioServerParameters or None if server not found
        """
        server = self.get_server(name)
        if not server:
            return None
        
        return StdioServerParameters(
            command=server["command"],
            args=server["args"],
            env=server.get("env")
        )


class MCPClient:
    """
    MCP Client for interacting with MCP servers
    
    Provides methods to connect to servers, discover tools, and execute tool calls
    """
    
    def __init__(self, registry: MCPServerRegistry):
        self.registry = registry
        self._sessions: Dict[str, ClientSession] = {}
    
    @asynccontextmanager
    async def connect_to_server(self, server_name: str):
        """
        Connect to an MCP server
        
        Args:
            server_name: Name of registered server
            
        Yields:
            ClientSession for the server
        """
        server_params = self.registry.get_server_params(server_name)
        if not server_params:
            raise ValueError(f"Server '{server_name}' not found in registry")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                yield session
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """
        List all tools available from an MCP server
        
        Args:
            server_name: Name of MCP server
            
        Returns:
            List of tool definitions
        """
        try:
            async with self.connect_to_server(server_name) as session:
                # List available tools
                tools_result = await session.list_tools()
                
                # Format tools for consumption
                tools = []
                for tool in tools_result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "server": server_name
                    })
                
                return tools
        
        except Exception as e:
            raise Exception(f"Failed to list tools from '{server_name}': {str(e)}")
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call a tool on an MCP server
        
        Args:
            server_name: Name of MCP server
            tool_name: Name of tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        try:
            async with self.connect_to_server(server_name) as session:
                # Call the tool
                result = await session.call_tool(tool_name, arguments)
                
                # Extract content from result
                if result.content:
                    # MCP returns content as a list of ContentItems
                    content_items = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content_items.append(item.text)
                        elif hasattr(item, 'data'):
                            content_items.append(item.data)
                        else:
                            content_items.append(str(item))
                    
                    return {
                        "success": True,
                        "content": content_items,
                        "isError": result.isError if hasattr(result, 'isError') else False
                    }
                else:
                    return {
                        "success": True,
                        "content": [],
                        "isError": False
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "isError": True
            }
    
    async def discover_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover tools from all registered servers
        
        Returns:
            Dictionary mapping server names to their tools
        """
        all_tools = {}
        
        for server in self.registry.list_servers():
            server_name = server["name"]
            try:
                tools = await self.list_tools(server_name)
                all_tools[server_name] = tools
            except Exception as e:
                # Log error but continue with other servers
                all_tools[server_name] = {
                    "error": str(e),
                    "tools": []
                }
        
        return all_tools
    
    async def get_tool_schema(
        self,
        server_name: str,
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a specific tool
        
        Args:
            server_name: Name of MCP server
            tool_name: Name of tool
            
        Returns:
            Tool schema or None if not found
        """
        try:
            tools = await self.list_tools(server_name)
            for tool in tools:
                if tool["name"] == tool_name:
                    return tool
            return None
        except Exception:
            return None


class MCPErrorHandler:
    """
    Error handling utilities for MCP operations
    """
    
    @staticmethod
    def handle_connection_error(server_name: str, error: Exception) -> Dict[str, Any]:
        """Handle MCP server connection errors"""
        return {
            "error": "connection_failed",
            "message": f"Failed to connect to MCP server '{server_name}'",
            "details": str(error),
            "server": server_name
        }
    
    @staticmethod
    def handle_tool_call_error(
        server_name: str,
        tool_name: str,
        error: Exception
    ) -> Dict[str, Any]:
        """Handle MCP tool call errors"""
        return {
            "error": "tool_call_failed",
            "message": f"Failed to call tool '{tool_name}' on server '{server_name}'",
            "details": str(error),
            "server": server_name,
            "tool": tool_name
        }
    
    @staticmethod
    def handle_discovery_error(server_name: str, error: Exception) -> Dict[str, Any]:
        """Handle tool discovery errors"""
        return {
            "error": "discovery_failed",
            "message": f"Failed to discover tools from server '{server_name}'",
            "details": str(error),
            "server": server_name
        }


# Global MCP registry and client instances
_mcp_registry = MCPServerRegistry()
_mcp_client = MCPClient(_mcp_registry)


def get_mcp_registry() -> MCPServerRegistry:
    """Get the global MCP server registry"""
    return _mcp_registry


def get_mcp_client() -> MCPClient:
    """Get the global MCP client"""
    return _mcp_client


# Helper functions for common operations

async def register_mcp_server(
    name: str,
    command: str,
    args: List[str] = None,
    env: Dict[str, str] = None,
    description: str = ""
) -> bool:
    """
    Register a new MCP server
    
    Args:
        name: Server identifier
        command: Command to start server
        args: Command arguments
        env: Environment variables
        description: Server description
        
    Returns:
        True if successful
    """
    try:
        registry = get_mcp_registry()
        registry.register_server(name, command, args, env, description)
        return True
    except Exception:
        return False


async def list_mcp_servers() -> List[Dict[str, Any]]:
    """
    List all registered MCP servers
    
    Returns:
        List of server configurations
    """
    registry = get_mcp_registry()
    return registry.list_servers()


async def list_mcp_tools(server_name: str) -> List[Dict[str, Any]]:
    """
    List tools from an MCP server
    
    Args:
        server_name: Name of server
        
    Returns:
        List of tools
    """
    client = get_mcp_client()
    return await client.list_tools(server_name)


async def call_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: Dict[str, Any]
) -> Any:
    """
    Call an MCP tool
    
    Args:
        server_name: Name of server
        tool_name: Name of tool
        arguments: Tool arguments
        
    Returns:
        Tool result
    """
    client = get_mcp_client()
    return await client.call_tool(server_name, tool_name, arguments)


async def discover_all_mcp_tools() -> Dict[str, List[Dict[str, Any]]]:
    """
    Discover all tools from all registered servers
    
    Returns:
        Dictionary mapping server names to tools
    """
    client = get_mcp_client()
    return await client.discover_all_tools()
