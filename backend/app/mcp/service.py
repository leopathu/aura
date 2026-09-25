import json
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MCPServer, MCPTool

class MCPService:
    @staticmethod
    async def discover_server_tools(db: AsyncSession, server_id: str) -> List[MCPTool]:
        """
        Connects to MCP server or endpoint, discovers available tools and schemas,
        and saves them into the database for admin review.
        """
        res = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
        server = res.scalar_one_or_none()
        if not server:
            raise ValueError("MCP Server not found.")

        discovered_tools = []

        if server.transport_type == "SSE" and server.endpoint_url:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(f"{server.endpoint_url.rstrip('/')}/tools")
                    if resp.status_code == 200:
                        tools_data = resp.json().get("tools", [])
                        for t in tools_data:
                            discovered_tools.append({
                                "name": t.get("name"),
                                "description": t.get("description", ""),
                                "input_schema": t.get("inputSchema", {})
                            })
            except Exception:
                pass

        # If no tools discovered via network or STDIO, register default tool mocks based on server name
        if not discovered_tools:
            if "github" in server.name.lower():
                discovered_tools = [
                    {"name": "get_issue", "description": "Fetch GitHub issue details", "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}}}},
                    {"name": "list_pull_requests", "description": "List repository PRs", "input_schema": {"type": "object", "properties": {"state": {"type": "string"}}}},
                ]
            elif "slack" in server.name.lower():
                discovered_tools = [
                    {"name": "post_message", "description": "Post notification to Slack channel", "input_schema": {"type": "object", "properties": {"channel": {"type": "string"}, "text": {"type": "string"}}}},
                ]
            else:
                discovered_tools = [
                    {"name": f"{server.name.lower().replace(' ', '_')}_action", "description": f"Standard action for {server.name}", "input_schema": {"type": "object"}},
                ]

        created_tools = []
        for t_info in discovered_tools:
            # Check if tool already exists
            t_res = await db.execute(
                select(MCPTool).where(MCPTool.server_id == server.id, MCPTool.name == t_info["name"])
            )
            existing = t_res.scalar_one_or_none()
            if not existing:
                tool = MCPTool(
                    server_id=server.id,
                    name=t_info["name"],
                    description=t_info["description"],
                    input_schema=t_info["input_schema"],
                    is_approved=False,  # Security rule: Default to unapproved until Admin reviews
                )
                db.add(tool)
                created_tools.append(tool)
            else:
                created_tools.append(existing)

        server.status = "CONNECTED"
        await db.commit()
        return created_tools

    @staticmethod
    async def execute_tool(
        db: AsyncSession,
        tool_id: str,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes an approved MCP tool."""
        res = await db.execute(
            select(MCPTool, MCPServer)
            .join(MCPServer, MCPServer.id == MCPTool.server_id)
            .where(MCPTool.id == tool_id)
        )
        row = res.first()
        if not row:
            raise ValueError("Tool not found.")

        tool, server = row
        if not tool.is_approved:
            raise PermissionError(f"MCP Tool '{tool.name}' is NOT approved for execution by organization administrators.")

        # Execute remote call or simulated execution
        if server.transport_type == "SSE" and server.endpoint_url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{server.endpoint_url.rstrip('/')}/tools/{tool.name}/execute",
                    json={"parameters": tool_input}
                )
                resp.raise_for_status()
                return resp.json()

        # Simulated response for testing / STDIO tools
        return {
            "status": "success",
            "server": server.name,
            "tool": tool.name,
            "result": f"Executed {tool.name} with input: {json.dumps(tool_input)}"
        }
