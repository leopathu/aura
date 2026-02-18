"""
API Version 1 Router
Combines all endpoint routers
"""

from fastapi import APIRouter
from app.api.v1 import auth, users, organizations, agents, chat, credentials, oauth, tools, integrations, mcp, agent_debug, approvals, activity, automations

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)
api_router.include_router(agents.router)
api_router.include_router(chat.router)
api_router.include_router(credentials.router)
api_router.include_router(oauth.router)
api_router.include_router(tools.router)
api_router.include_router(integrations.router)
api_router.include_router(mcp.router)
api_router.include_router(agent_debug.router)
api_router.include_router(approvals.router)
api_router.include_router(activity.router)
api_router.include_router(automations.router)

@api_router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "message": "Aura API v1",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/health"
        }
    }
