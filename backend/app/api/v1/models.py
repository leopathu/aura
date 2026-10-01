from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.crypto import encrypt_secret
from app.models import AIProvider, AIModel, User
from app.schemas.domain import (
    AIProviderCreate,
    AIProviderResponse,
    AIModelCreate,
    AIModelResponse,
)
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.models_ai.factory import get_llm_provider

router = APIRouter(prefix="/models", tags=["AI Models & Providers"])

# -------------------------------------------------------------
# AI Providers
# -------------------------------------------------------------
@router.get("/providers", response_model=List[AIProviderResponse])
async def list_providers(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AIProvider, func.count(AIModel.id).label("models_count"))
        .outerjoin(AIModel, AIModel.provider_id == AIProvider.id)
        .where(AIProvider.organization_id == org_id)
        .group_by(AIProvider.id)
        .order_by(AIProvider.created_at.desc())
    )
    res = await db.execute(stmt)
    results = []
    for prov, count in res.all():
        results.append(
            AIProviderResponse(
                id=prov.id,
                name=prov.name,
                provider_type=prov.provider_type,
                base_url=prov.base_url,
                is_active=prov.is_active,
                models_count=count
            )
        )
    return results

@router.post("/providers", dependencies=[Depends(require_permission("admin.models"))])
async def create_provider(
    payload: AIProviderCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    encrypted_key = encrypt_secret(payload.api_key) if payload.api_key else None
    provider_type_clean = payload.provider_type.upper().strip()
    
    # Sensible default base_url per provider type if not explicitly passed
    base_url = payload.base_url
    if not base_url:
        if provider_type_clean == "OPENAI":
            base_url = "https://api.openai.com/v1"
        elif provider_type_clean == "ANTHROPIC":
            base_url = "https://api.anthropic.com"
        elif provider_type_clean == "OLLAMA":
            base_url = "http://localhost:11434"

    provider = AIProvider(
        organization_id=org_id,
        name=payload.name,
        provider_type=provider_type_clean,
        base_url=base_url,
        encrypted_api_key=encrypted_key,
        is_active=True
    )
    db.add(provider)
    await db.flush()

    # Determine default chat model
    if provider_type_clean == "OPENAI":
        default_chat_id = "gpt-4o"
        default_embed_id = "text-embedding-3-small"
    elif provider_type_clean == "ANTHROPIC":
        default_chat_id = "claude-3-5-sonnet-20241022"
        default_embed_id = None
    elif provider_type_clean == "OLLAMA":
        default_chat_id = "llama3.1"
        default_embed_id = "nomic-embed-text"
    elif provider_type_clean == "MOCK":
        default_chat_id = "mock-gpt-4"
        default_embed_id = "mock-embedding"
    else:
        default_chat_id = "custom-chat"
        default_embed_id = None

    # Check if there is already a default chat model in the organization
    existing_chat_def = (await db.execute(
        select(AIModel.id)
        .join(AIProvider)
        .where(
            AIProvider.organization_id == org_id,
            AIModel.model_type == "CHAT",
            AIModel.is_default == True
        )
    )).first()

    chat_model = AIModel(
        provider_id=provider.id,
        name=f"{payload.name} Chat ({default_chat_id})",
        model_id=default_chat_id,
        model_type="CHAT",
        context_window=128000 if provider_type_clean != "ANTHROPIC" else 200000,
        is_default=True if not existing_chat_def else False
    )
    db.add(chat_model)

    if default_embed_id:
        existing_embed_def = (await db.execute(
            select(AIModel.id)
            .join(AIProvider)
            .where(
                AIProvider.organization_id == org_id,
                AIModel.model_type == "EMBEDDING",
                AIModel.is_default == True
            )
        )).first()

        embed_model = AIModel(
            provider_id=provider.id,
            name=f"{payload.name} Embedding ({default_embed_id})",
            model_id=default_embed_id,
            model_type="EMBEDDING",
            context_window=8192,
            is_default=True if not existing_embed_def else False
        )
        db.add(embed_model)

    await db.commit()
    await db.refresh(provider)
    return {"id": provider.id, "name": provider.name, "provider_type": provider.provider_type}

@router.delete("/providers/{id}", dependencies=[Depends(require_permission("admin.models"))])
async def delete_provider(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AIProvider).where(AIProvider.id == id, AIProvider.organization_id == org_id)
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI Provider not found")

    await db.delete(provider)
    await db.commit()
    return {"status": "success", "message": "Provider deleted successfully"}

@router.get("/providers/{id}/available-models")
async def get_provider_available_models(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AIProvider).where(AIProvider.id == id, AIProvider.organization_id == org_id)
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    llm = get_llm_provider(provider)
    models = await llm.get_available_models()
    return {
        "provider_id": provider.id,
        "provider_name": provider.name,
        "provider_type": provider.provider_type,
        "models": models
    }

@router.post("/providers/{id}/test", dependencies=[Depends(require_permission("admin.models"))])
async def test_provider(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AIProvider).where(AIProvider.id == id, AIProvider.organization_id == org_id)
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Pick appropriate model tag to test
    test_model = "gpt-4o"
    if provider.provider_type == "ANTHROPIC":
        test_model = "claude-3-5-sonnet-20241022"
    elif provider.provider_type == "OLLAMA":
        test_model = "llama3.1"
    elif provider.provider_type == "MOCK":
        test_model = "mock-gpt-4"

    # If provider has configured models in DB, use the first one
    model_res = await db.execute(
        select(AIModel).where(AIModel.provider_id == provider.id, AIModel.model_type == "CHAT").limit(1)
    )
    configured_model = model_res.scalar_one_or_none()
    if configured_model:
        test_model = configured_model.model_id

    # Specialized health verification for Ollama
    if provider.provider_type == "OLLAMA":
        from app.models_ai.providers import OllamaProvider
        ollama = OllamaProvider(base_url=provider.base_url)
        try:
            health = await ollama.check_health()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Connection failed: Cannot reach Ollama at '{provider.base_url or 'http://localhost:11434'}'. Ensure Ollama daemon is running (`ollama serve`). Detail: {str(e)}"
            }

        installed_models = health.get("models", [])
        if not installed_models:
            return {
                "status": "success",
                "message": f"Connection verified! Ollama is running and accessible at '{provider.base_url or 'http://localhost:11434'}'. (Notice: No models have been pulled yet. Run `ollama pull llama3.1` in your terminal, then register it in Aura).",
                "sample_response": "Online (0 models installed)"
            }

        # Check if configured model or test model exists in installed models
        matched_model = None
        for m in installed_models:
            if m == test_model or m.startswith(f"{test_model}:") or test_model in m:
                matched_model = m
                break

        chosen_model = matched_model or installed_models[0]
        try:
            reply = await ollama.chat(
                messages=[{"role": "user", "content": "Ping test"}],
                model=chosen_model,
                max_tokens=20
            )
            note = f" (Verified using installed model '{chosen_model}')"
            if matched_model is None:
                note += f". Note: '{test_model}' is not pulled; available models: {', '.join(installed_models[:3])}"
            return {
                "status": "success",
                "message": f"Connection verified successfully!{note}",
                "sample_response": reply
            }
        except Exception as e:
            return {
                "status": "success",
                "message": f"Ollama is online at '{provider.base_url}' with {len(installed_models)} model(s): {', '.join(installed_models[:4])}. (Chat test note: {str(e)})",
                "sample_response": f"{len(installed_models)} models detected"
            }

    # For other providers (OpenAI, Anthropic, Custom, Mock)
    llm = get_llm_provider(provider)
    try:
        reply = await llm.chat(
            messages=[{"role": "user", "content": "Ping test"}],
            model=test_model,
            max_tokens=20
        )
        return {"status": "success", "message": f"Connection verified with model '{test_model}'", "sample_response": reply}
    except Exception as e:
        return {"status": "error", "message": f"Connection test failed: {str(e)}"}


# -------------------------------------------------------------
# AI Models (Chat & Embedding Models)
# -------------------------------------------------------------
@router.get("", response_model=List[AIModelResponse])
async def list_models(
    model_type: Optional[str] = None,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(AIModel)
        .join(AIProvider, AIProvider.id == AIModel.provider_id)
        .options(selectinload(AIModel.provider))
        .where(AIProvider.organization_id == org_id)
    )
    if model_type:
        stmt = stmt.where(AIModel.model_type == model_type.upper())
    stmt = stmt.order_by(AIModel.is_default.desc(), AIModel.created_at.desc())

    res = await db.execute(stmt)
    models = res.scalars().all()
    
    return [
        AIModelResponse(
            id=m.id,
            provider_id=m.provider_id,
            provider_name=m.provider.name if m.provider else None,
            provider_type=m.provider.provider_type if m.provider else None,
            name=m.name,
            model_id=m.model_id,
            model_type=m.model_type,
            context_window=m.context_window,
            is_default=m.is_default,
            created_at=m.created_at
        )
        for m in models
    ]

@router.post("", response_model=AIModelResponse, dependencies=[Depends(require_permission("admin.models"))])
async def create_model(
    payload: AIModelCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    # Verify provider belongs to organization
    res = await db.execute(
        select(AIProvider).where(AIProvider.id == payload.provider_id, AIProvider.organization_id == org_id)
    )
    provider = res.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="AI Provider not found in this organization")

    model_type_clean = payload.model_type.upper().strip()

    # If marked as default, clear existing default for this model_type across org's providers
    if payload.is_default:
        await db.execute(
            update(AIModel)
            .where(
                AIModel.provider_id.in_(
                    select(AIProvider.id).where(AIProvider.organization_id == org_id)
                ),
                AIModel.model_type == model_type_clean
            )
            .values(is_default=False)
        )

    model = AIModel(
        provider_id=provider.id,
        name=payload.name.strip(),
        model_id=payload.model_id.strip(),
        model_type=model_type_clean,
        context_window=payload.context_window or 128000,
        is_default=bool(payload.is_default)
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)

    return AIModelResponse(
        id=model.id,
        provider_id=model.provider_id,
        provider_name=provider.name,
        provider_type=provider.provider_type,
        name=model.name,
        model_id=model.model_id,
        model_type=model.model_type,
        context_window=model.context_window,
        is_default=model.is_default,
        created_at=model.created_at
    )

@router.delete("/{id}", dependencies=[Depends(require_permission("admin.models"))])
async def delete_model(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AIModel)
        .join(AIProvider, AIProvider.id == AIModel.provider_id)
        .where(AIModel.id == id, AIProvider.organization_id == org_id)
    )
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="AI Model not found")

    await db.delete(model)
    await db.commit()
    return {"status": "success", "message": "Model deleted successfully"}

@router.post("/{id}/set-default", dependencies=[Depends(require_permission("admin.models"))])
async def set_default_model(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AIModel)
        .join(AIProvider, AIProvider.id == AIModel.provider_id)
        .options(selectinload(AIModel.provider))
        .where(AIModel.id == id, AIProvider.organization_id == org_id)
    )
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="AI Model not found")

    # Unset is_default on other models with same model_type
    await db.execute(
        update(AIModel)
        .where(
            AIModel.provider_id.in_(
                select(AIProvider.id).where(AIProvider.organization_id == org_id)
            ),
            AIModel.model_type == model.model_type
        )
        .values(is_default=False)
    )

    model.is_default = True
    await db.commit()
    return {
        "status": "success",
        "message": f"'{model.name}' is now the default {model.model_type.lower()} model",
        "id": model.id,
        "is_default": True
    }
