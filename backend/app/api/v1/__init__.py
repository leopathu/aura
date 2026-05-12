"""API v1 router — aggregates all v1 sub-routers."""

from fastapi import APIRouter

from app.api.v1.agent_chat import router as agent_chat_router
from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.brains import router as brains_router
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.query import router as query_router
from app.api.v1.settings import router as settings_router

api_router = APIRouter()

api_router.include_router(agent_chat_router)
api_router.include_router(agents_router)
api_router.include_router(auth_router)
api_router.include_router(brains_router)
api_router.include_router(chat_router)
api_router.include_router(documents_router)
api_router.include_router(query_router)
api_router.include_router(settings_router)

