import pytest
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import verify_password, create_access_token, decode_token
from app.rbac.service import RBACService
from app.policies.sql_validator import SQLSecurityLayer, SQLValidationError
from app.policies.policy_engine import PolicyEngine
from app.connectors.sqlite import SQLiteConnector
from app.tools.registry import tool_registry
from app.agent.runtime import AgentRuntime
from app.models import Organization, User, DataSource, Document
from sqlalchemy import select

@pytest.mark.asyncio
async def test_auth_tokens():
    token = create_access_token("test-user-id")
    payload = decode_token(token)
    assert payload["sub"] == "test-user-id"
    assert payload["type"] == "access"

@pytest.mark.asyncio
async def test_sql_security_layer():
    # 1. Valid SELECT should pass
    expr, tables, columns = SQLSecurityLayer.parse_and_validate(
        "SELECT id, name, email FROM customers WHERE country = 'India'"
    )
    assert "customers" in tables
    assert "id" in columns or "name" in columns

    # 2. Enforce limits
    safe_sql = SQLSecurityLayer.enforce_limits_and_safety(expr, max_rows=100)
    assert "LIMIT" in safe_sql.upper()

    # 3. Forbidden DML/DDL must raise error
    with pytest.raises(SQLValidationError):
        SQLSecurityLayer.parse_and_validate("DROP TABLE customers;")

    with pytest.raises(SQLValidationError):
        SQLSecurityLayer.parse_and_validate("DELETE FROM customers WHERE id = 1;")

    with pytest.raises(SQLValidationError):
        SQLSecurityLayer.parse_and_validate("UPDATE customers SET annual_spend = 0;")

    with pytest.raises(SQLValidationError):
        SQLSecurityLayer.parse_and_validate("INSERT INTO customers VALUES (5, 'Bad', 'bad@bad.com', 'US', 0);")

@pytest.mark.asyncio
async def test_policy_engine_and_masking():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Organization).where(Organization.slug == "acme-corp"))
        org = res.scalar_one_or_none()
        assert org is not None

        # Test data masking helper
        raw_rows = [{"id": 1, "name": "Alice", "email": "alice@example.com", "salary": 120000}]
        masking_rules = {"email": "MASK_EMAIL", "salary": "REDACT"}
        masked = PolicyEngine.apply_data_masking(raw_rows, masking_rules)
        assert "@" in masked[0]["email"] and "***" in masked[0]["email"]
        assert masked[0]["salary"] == "[REDACTED]"

@pytest.mark.asyncio
async def test_sqlite_connector_and_tool():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(DataSource).where(DataSource.name == "Sales & Transactions DB"))
        source = res.scalar_one_or_none()
        assert source is not None

        # Schema discovery
        schema_tool = tool_registry.get_tool("inspect_database_schema")
        ctx = {"db": db, "organization_id": source.organization_id}
        schema_res = await schema_tool.execute(ctx, source_id=source.id)
        assert schema_res.success is True
        table_names = [t["table_name"] for t in schema_res.data]
        assert "customers" in table_names
        assert "orders" in table_names

@pytest.mark.asyncio
async def test_agent_runtime_execution():
    async with AsyncSessionLocal() as db:
        u_res = await db.execute(select(User).where(User.email == "admin@acme.com"))
        user = u_res.scalar_one_or_none()
        assert user is not None

        o_res = await db.execute(select(Organization).where(Organization.slug == "acme-corp"))
        org = o_res.scalar_one_or_none()
        assert org is not None

        # Create temporary conversation
        from app.models import Conversation
        conv = Conversation(organization_id=org.id, user_id=user.id, title="Test Run")
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

        runtime = AgentRuntime(db)
        events = []
        async for chunk in runtime.execute_stream(
            conversation_id=conv.id,
            user_id=user.id,
            organization_id=org.id,
            user_request="How much revenue did we make this quarter and what is our employee leave policy?"
        ):
            events.append(chunk)

        assert any("event: run_started" in e for e in events)
        assert any("event: step" in e for e in events)
        assert any("event: done" in e for e in events)

@pytest.mark.asyncio
async def test_brain_access_control_and_scoping():
    from app.brains.service import BrainService
    from app.models import Brain, BrainRole, Role
    from app.schemas.domain import BrainCreate

    async with AsyncSessionLocal() as db:
        o_res = await db.execute(select(Organization).where(Organization.slug == "acme-corp"))
        org = o_res.scalar_one_or_none()
        assert org is not None

        # Admin user
        admin_res = await db.execute(select(User).where(User.email == "admin@acme.com"))
        admin_user = admin_res.scalar_one_or_none()

        # Analyst user
        analyst_res = await db.execute(select(User).where(User.email == "analyst@acme.com"))
        analyst_user = analyst_res.scalar_one_or_none()

        # 1. Admin should have unrestricted access (returns None)
        admin_accessible = await BrainService.get_user_accessible_brain_ids(db, admin_user.id, org.id)
        assert admin_accessible is None

        # 2. Analyst should have access only to assigned brains
        analyst_accessible = await BrainService.get_user_accessible_brain_ids(db, analyst_user.id, org.id)
        assert analyst_accessible is not None
        assert len(analyst_accessible) > 0

        # 3. Create a restricted private Brain with NO roles assigned
        private_brain = await BrainService.create_brain(
            db=db,
            organization_id=org.id,
            name="Executive Confidential Brain",
            description="Confidential strategy documents and M&A data",
            role_ids=[]
        )
        assert private_brain.id is not None

        # 4. Analyst should NOT have access to the newly created private brain
        analyst_accessible_updated = await BrainService.get_user_accessible_brain_ids(db, analyst_user.id, org.id)
        assert private_brain.id not in analyst_accessible_updated

        # 5. Assign Analyst role to the private brain
        analyst_role = (await db.execute(
            select(Role).where(Role.organization_id == org.id, Role.name == "Analyst")
        )).scalar_one_or_none()
        assert analyst_role is not None

        await BrainService.update_brain_roles(db, private_brain.id, [analyst_role.id])

        # 6. Now Analyst should have access
        analyst_accessible_after = await BrainService.get_user_accessible_brain_ids(db, analyst_user.id, org.id)
        assert private_brain.id in analyst_accessible_after
