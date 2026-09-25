from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.crypto import encrypt_secret
from app.models import AIProvider, AIModel, User
from app.schemas.domain import AIProviderCreate, AIProviderResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.models_ai.factory import get_llm_provider

router = APIRouter(prefix="/models", tags=["AI Models & Providers"])

@router.get("/providers", response_model=List[AIProviderResponse])
async def list_providers(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AIProvider).where(AIProvider.organization_id == org_id))
    return res.scalars().all()

@router.post("/providers", dependencies=[Depends(require_permission("admin.models"))])
async def create_provider(
    payload: AIProviderCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    encrypted_key = encrypt_secret(payload.api_key) if payload.api_key else None
    provider = AIProvider(
        organization_id=org_id,
        name=payload.name,
        provider_type=payload.provider_type.upper(),
        base_url=payload.base_url,
        encrypted_api_key=encrypted_key,
        is_active=True
    )
    db.add(provider)
    await db.flush()

    # Add default model
    default_model_name = "gpt-4o" if "openai" in payload.provider_type.lower() else "default-model"
    model = AIModel(
        provider_id=provider.id,
        name=f"{payload.name} Chat",
        model_id=default_model_name,
        model_type="CHAT",
        is_default=True
    )
    db.add(model)
    await db.commit()
    await db.refresh(provider)
    return {"id": provider.id, "name": provider.name, "provider_type": provider.provider_type}

@router.post("/providers/{id}/test", dependencies=[Depends(require_permission("admin.models"))])
async def test_provider(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AIProvider).where(AIProvider.id == id, AIProvider.organization_id == org_id))
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    llm = get_llm_provider(provider)
    try:
        reply = await llm.chat(
            messages=[{"role": "user", "content": "Ping test"}],
            model="gpt-4o",
            max_tokens=20
        )
        return {"status": "success", "message": "Connection verified successfully", "sample_response": reply}
    except Exception as e:
        return {"status": "error", "message": f"Connection test failed: {str(e)}"}
