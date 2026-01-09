"""
MCP (Model Context Protocol) Client Service
Handles connections to MCP servers and tool execution
"""
from typing import Dict, List, Any, Optional
import httpx
import json
from pydantic import BaseModel

class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPClient:
    """Client for interacting with MCP servers."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools: List[MCPTool] = []
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def connect(self) -> bool:
        """Connect to MCP server and discover available tools."""
        try:
            response = await self.client.post(
                f"{self.server_url}/initialize",
                json={
                    "protocolVersion": "1.0",
                    "capabilities": {
                        "tools": {}
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # Store server capabilities
                return True
            return False
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    async def list_tools(self) -> List[MCPTool]:
        """Get list of available tools from MCP server."""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/list",
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                self.tools = [MCPTool(**tool) for tool in tools]
                return self.tools
            return []
        except Exception as e:
            print(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool with given arguments."""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Tool call failed with status {response.status_code}",
                    "content": []
                }
        except Exception as e:
            return {
                "error": f"Tool call failed: {str(e)}",
                "content": []
            }
    
    async def disconnect(self):
        """Close connection to MCP server."""
        await self.client.aclose()

class MCPRegistry:
    """Registry for managing multiple MCP connections."""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    async def register_server(self, name: str, server_url: str) -> bool:
        """Register a new MCP server."""
        client = MCPClient(server_url)
        connected = await client.connect()
        
        if connected:
            self.clients[name] = client
            await client.list_tools()
            return True
        return False
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """Get an MCP client by name."""
        return self.clients.get(name)
    
    async def get_all_tools(self) -> Dict[str, List[MCPTool]]:
        """Get all available tools from all registered servers."""
        all_tools = {}
        for name, client in self.clients.items():
            all_tools[name] = client.tools
        return all_tools
    
    async def disconnect_all(self):
        """Disconnect all MCP clients."""
        for client in self.clients.values():
            await client.disconnect()

# Global registry instance
mcp_registry = MCPRegistry()
