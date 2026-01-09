from fastapi import APIRouter
from app.api.v1.endpoints import auth, organizations, credentials, agents, chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(credentials.router, prefix="/organizations/{org_id}/credentials", tags=["Credentials"])
api_router.include_router(agents.router, prefix="/organizations/{org_id}/agents", tags=["Agents"])
api_router.include_router(chat.router, tags=["Chat"])
