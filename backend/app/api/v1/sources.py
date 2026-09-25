from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.crypto import encrypt_secret
from app.models import (
    DataSource,
    DataSourceCredential,
    DataSourceSchema,
    DataSourceTable,
    DataSourceColumn,
    User,
    AuditLog,
)
from app.schemas.domain import DataSourceCreate, DataSourceResponse, DirectQueryRequest
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.connectors.factory import get_data_connector
from app.policies.policy_engine import PolicyEngine
from app.worker.tasks import run_schema_discovery_job

router = APIRouter(prefix="/sources", tags=["Data Sources"])

@router.get("", response_model=List[DataSourceResponse])
async def list_data_sources(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(DataSource).where(DataSource.organization_id == org_id))
    return res.scalars().all()

@router.post("", dependencies=[Depends(require_permission("source.create"))])
async def create_data_source(
    payload: DataSourceCreate,
    background_tasks: BackgroundTasks,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    source = DataSource(
        organization_id=org_id,
        name=payload.name,
        type=payload.type.upper(),
        description=payload.description,
        is_active=True,
        is_read_only=payload.is_read_only,
    )
    db.add(source)
    await db.flush()

    cred = DataSourceCredential(
        data_source_id=source.id,
        encrypted_connection_uri=encrypt_secret(payload.connection_uri)
    )
    db.add(cred)
    await db.commit()
    await db.refresh(source)

    # Trigger schema discovery in background
    background_tasks.add_task(run_schema_discovery_job, source.id)

    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="DATABASE_CONNECTED",
        resource_type="DATABASE",
        resource_id=source.id,
        status="SUCCESS",
        metadata_json={"source_name": source.name, "type": source.type}
    )
    db.add(audit)
    await db.commit()

    return {"id": source.id, "name": source.name, "type": source.type, "message": "Source created and schema discovery initiated"}

@router.post("/{id}/test")
async def test_source_connection(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(DataSource, DataSourceCredential)
        .join(DataSourceCredential, DataSourceCredential.data_source_id == DataSource.id)
        .where(DataSource.id == id, DataSource.organization_id == org_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Data source not found")
    source, cred = row

    try:
        connector = get_data_connector(source, cred)
        connected = await connector.test_connection()
        await connector.close()
        if connected:
            return {"status": "success", "message": f"Successfully connected to {source.name}"}
        else:
            return {"status": "error", "message": "Could not connect to database with provided URI"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/{id}/sync-schema", dependencies=[Depends(require_permission("source.update"))])
async def sync_schema(
    id: str,
    background_tasks: BackgroundTasks,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    background_tasks.add_task(run_schema_discovery_job, id)
    return {"status": "queued", "message": "Schema discovery queued for background execution"}

@router.get("/{id}/schema")
async def get_source_schema(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    schema_res = await db.execute(
        select(DataSourceSchema).where(DataSourceSchema.data_source_id == id)
    )
    schema = schema_res.scalar_one_or_none()
    if not schema:
        return {"tables": []}

    tables_res = await db.execute(
        select(DataSourceTable).where(DataSourceTable.schema_id == schema.id)
    )
    tables = tables_res.scalars().all()

    output = []
    for t in tables:
        cols_res = await db.execute(
            select(DataSourceColumn).where(DataSourceColumn.table_id == t.id)
        )
        cols = cols_res.scalars().all()
        output.append({
            "id": t.id,
            "table_name": t.table_name,
            "row_count": t.row_count,
            "columns": [
                {
                    "name": c.column_name,
                    "data_type": c.data_type,
                    "is_nullable": c.is_nullable,
                    "is_primary_key": c.is_primary_key
                }
                for c in cols
            ]
        })
    return {"tables": output}

@router.post("/{id}/query", dependencies=[Depends(require_permission("database.query"))])
async def execute_direct_query(
    id: str,
    payload: DirectQueryRequest,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(DataSource, DataSourceCredential)
        .join(DataSourceCredential, DataSourceCredential.data_source_id == DataSource.id)
        .where(DataSource.id == id, DataSource.organization_id == org_id)
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Data source not found")
    source, cred = row

    # 1. Enforce policy engine
    eval_result = await PolicyEngine.evaluate_sql_query(
        db=db,
        organization_id=org_id,
        user_id=current_user.id,
        raw_sql=payload.sql_query
    )
    if not eval_result.allowed:
        raise HTTPException(status_code=403, detail=f"Policy Denied: {eval_result.reason}")

    connector = get_data_connector(source, cred)
    try:
        raw_rows = await connector.execute_query(eval_result.rewritten_sql)
        masked_rows = PolicyEngine.apply_data_masking(raw_rows, eval_result.masking_rules)
        return {
            "success": True,
            "rows": masked_rows,
            "count": len(masked_rows),
            "executed_sql": eval_result.rewritten_sql
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await connector.close()
