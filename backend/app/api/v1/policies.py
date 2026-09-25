from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Policy, PolicyRule, User, Role
from app.schemas.domain import PolicyCreate, PolicyResponse, PolicyRuleCreate
from app.api.deps import get_current_user, get_current_organization_id, require_permission

router = APIRouter(prefix="/policies", tags=["Policies & Security Rules"])

@router.get("", response_model=List[PolicyResponse])
async def list_policies(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Policy).where(Policy.organization_id == org_id))
    policies = res.scalars().all()
    output = []
    for p in policies:
        rules_res = await db.execute(select(PolicyRule).where(PolicyRule.policy_id == p.id))
        rules = rules_res.scalars().all()
        output.append(
            PolicyResponse(
                id=p.id,
                organization_id=p.organization_id,
                name=p.name,
                description=p.description,
                is_active=p.is_active,
                rules=[
                    {
                        "id": r.id,
                        "role_id": r.role_id,
                        "resource_type": r.resource_type,
                        "resource_name": r.resource_name,
                        "effect": r.effect,
                        "row_filter_expr": r.row_filter_expr,
                        "allowed_columns": r.allowed_columns,
                        "data_masking_rule": r.data_masking_rule
                    }
                    for r in rules
                ]
            )
        )
    return output

@router.post("", dependencies=[Depends(require_permission("admin.policies"))])
async def create_policy(
    payload: PolicyCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    policy = Policy(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        is_active=True
    )
    db.add(policy)
    await db.flush()

    for r_in in payload.rules:
        rule = PolicyRule(
            policy_id=policy.id,
            role_id=r_in.role_id,
            resource_type=r_in.resource_type.upper(),
            resource_name=r_in.resource_name,
            effect=r_in.effect.upper(),
            row_filter_expr=r_in.row_filter_expr,
            allowed_columns=r_in.allowed_columns,
            data_masking_rule=r_in.data_masking_rule,
        )
        db.add(rule)

    await db.commit()
    await db.refresh(policy)
    return {"id": policy.id, "name": policy.name, "message": "Security policy created"}

@router.post("/{id}/rules", dependencies=[Depends(require_permission("admin.policies"))])
async def add_policy_rule(
    id: str,
    payload: PolicyRuleCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Policy).where(Policy.id == id, Policy.organization_id == org_id))
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    rule = PolicyRule(
        policy_id=policy.id,
        role_id=payload.role_id,
        resource_type=payload.resource_type.upper(),
        resource_name=payload.resource_name,
        effect=payload.effect.upper(),
        row_filter_expr=payload.row_filter_expr,
        allowed_columns=payload.allowed_columns,
        data_masking_rule=payload.data_masking_rule,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"id": rule.id, "message": "Policy rule added successfully"}

@router.delete("/rules/{rule_id}", dependencies=[Depends(require_permission("admin.policies"))])
async def delete_policy_rule(
    rule_id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(PolicyRule)
        .join(Policy, Policy.id == PolicyRule.policy_id)
        .where(PolicyRule.id == rule_id, Policy.organization_id == org_id)
    )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")

    await db.delete(rule)
    await db.commit()
    return {"status": "success", "message": "Rule removed"}
