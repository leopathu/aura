from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import MCPServer, MCPTool, User
from app.schemas.domain import MCPServerCreate, MCPServerResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.mcp.service import MCPService

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MCPServer).where(MCPServer.organization_id == org_id))
    servers = res.scalars().all()
    output = []
    for s in servers:
        t_res = await db.execute(select(MCPTool).where(MCPTool.server_id == s.id))
        tools = t_res.scalars().all()
        output.append(
            MCPServerResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                transport_type=s.transport_type,
                endpoint_url=s.endpoint_url,
                status=s.status,
                tools=[
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                        "is_approved": t.is_approved
                    }
                    for t in tools
                ]
            )
        )
    return output

@router.post("/servers", dependencies=[Depends(require_permission("mcp.manage"))])
async def create_mcp_server(
    payload: MCPServerCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    server = MCPServer(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        transport_type=payload.transport_type.upper(),
        endpoint_url=payload.endpoint_url,
        command=payload.command,
        status="CONNECTED"
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)

    # Automatically discover initial tools
    await MCPService.discover_server_tools(db, server.id)

    return {"id": server.id, "name": server.name, "message": "MCP Server registered and tools discovered"}

@router.post("/servers/{id}/discover", dependencies=[Depends(require_permission("mcp.manage"))])
async def discover_tools(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(MCPServer).where(MCPServer.id == id, MCPServer.organization_id == org_id))
    server = res.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")

    tools = await MCPService.discover_server_tools(db, server.id)
    return {"status": "success", "tools_count": len(tools)}

@router.put("/tools/{tool_id}/approve", dependencies=[Depends(require_permission("mcp.manage"))])
async def toggle_tool_approval(
    tool_id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(MCPTool, MCPServer)
        .join(MCPServer, MCPServer.id == MCPTool.server_id)
        .where(MCPTool.id == tool_id, MCPServer.organization_id == org_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool, server = row

    tool.is_approved = not tool.is_approved
    await db.commit()
    return {
        "id": tool.id,
        "name": tool.name,
        "is_approved": tool.is_approved,
        "message": f"Tool '{tool.name}' approval set to {tool.is_approved}"
    }
