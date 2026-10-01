from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import User
from app.api.deps import get_current_user, get_current_organization_id
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as org_router
from app.api.v1.rbac import router as rbac_router
from app.api.v1.models import router as models_router
from app.api.v1.sources import router as sources_router
from app.api.v1.documents import router as documents_router
from app.api.v1.policies import router as policies_router
from app.api.v1.mcp import router as mcp_router
from app.api.v1.chat import router as chat_router
from app.api.v1.reports import router as reports_router
from app.api.v1.audit import router as audit_router
from app.api.v1.agent_runs import router as agent_runs_router
from app.api.v1.brains import router as brains_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(org_router)
api_v1_router.include_router(rbac_router)
api_v1_router.include_router(brains_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(sources_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(mcp_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(agent_runs_router)

@api_v1_router.get("/roles", tags=["RBAC & Permissions"])
async def list_roles_alias(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from app.api.v1.rbac import list_roles
    return await list_roles(org_id=org_id, current_user=current_user, db=db)

