import os
import sqlite3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.core.crypto import encrypt_secret
from app.models import (
    Organization,
    User,
    OrganizationUser,
    Role,
    AIProvider,
    AIModel,
    DataSource,
    DataSourceCredential,
    DataSourceSchema,
    DataSourceTable,
    DataSourceColumn,
    Document,
    DocumentChunk,
    Policy,
    PolicyRule,
    MCPServer,
    MCPTool
)
from app.rbac.service import RBACService
from app.worker.tasks import run_schema_discovery_job, run_document_ingestion_job

async def seed_initial_demo_data():
    """Initializes standard demonstration data for immediate out-of-the-box usage."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. System permissions
        await RBACService.init_system_permissions(db)

        # 2. Check if default Organization exists
        res = await db.execute(select(Organization).where(Organization.slug == "acme-corp"))
        org = res.scalar_one_or_none()
        if not org:
            org = Organization(name="Acme Corporation", slug="acme-corp")
            db.add(org)
            await db.flush()

            # Seed roles
            await RBACService.init_organization_roles(db, org.id)

            # 3. Create Admin User
            admin_user = User(
                email="admin@acme.com",
                password_hash=get_password_hash("admin123"),
                name="Aura Admin",
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            await db.flush()

            admin_role = (await db.execute(
                select(Role).where(Role.organization_id == org.id, Role.name == "Organization Admin")
            )).scalar_one_or_none()

            db.add(OrganizationUser(
                organization_id=org.id,
                user_id=admin_user.id,
                role_id=admin_role.id if admin_role else None,
                status="ACTIVE"
            ))

            # 4. Create Analyst User
            analyst_user = User(
                email="analyst@acme.com",
                password_hash=get_password_hash("analyst123"),
                name="Sarah Analyst",
                is_active=True
            )
            db.add(analyst_user)
            await db.flush()

            analyst_role = (await db.execute(
                select(Role).where(Role.organization_id == org.id, Role.name == "Analyst")
            )).scalar_one_or_none()

            db.add(OrganizationUser(
                organization_id=org.id,
                user_id=analyst_user.id,
                role_id=analyst_role.id if analyst_role else None,
                status="ACTIVE"
            ))

            # 5. Create default AI Provider (Mock / OpenAI compatible)
            ai_prov = AIProvider(
                organization_id=org.id,
                name="Mock Enterprise AI Gateway",
                provider_type="MOCK",
                base_url="https://api.openai.com/v1",
                is_active=True
            )
            db.add(ai_prov)
            await db.flush()

            db.add(AIModel(
                provider_id=ai_prov.id,
                name="Default Reasoning Engine",
                model_id="gpt-4o",
                model_type="CHAT",
                is_default=True
            ))

            # 6. Create sample SQLite demo database for SQL querying
            demo_db_path = os.path.abspath("./demo_sales.db")
            _create_local_demo_sqlite(demo_db_path)

            sample_source = DataSource(
                organization_id=org.id,
                name="Sales & Transactions DB",
                type="SQLITE",
                description="Production mirror of customer transactions, revenue, and product catalogs",
                is_active=True,
                is_read_only=True
            )
            db.add(sample_source)
            await db.flush()

            db.add(DataSourceCredential(
                data_source_id=sample_source.id,
                encrypted_connection_uri=encrypt_secret(f"sqlite:///{demo_db_path}")
            ))

            # 7. Create sample policy with Data Masking & Table rules
            policy = Policy(
                organization_id=org.id,
                name="Financial Security & PII Protection Policy",
                description="Restricts employee salary columns, masks customer emails, enforces row limits",
                is_active=True
            )
            db.add(policy)
            await db.flush()

            # Rule: Mask customer emails
            db.add(PolicyRule(
                policy_id=policy.id,
                resource_type="COLUMN",
                resource_name="email",
                effect="ALLOW",
                data_masking_rule="MASK_EMAIL"
            ))

            # Rule: Restrict salary
            db.add(PolicyRule(
                policy_id=policy.id,
                role_id=analyst_role.id if analyst_role else None,
                resource_type="COLUMN",
                resource_name="salary",
                effect="DENY"
            ))

            # 8. Create sample Company Policy document in storage
            sample_doc_dir = os.path.abspath("./storage/demo")
            os.makedirs(sample_doc_dir, exist_ok=True)
            doc_file = os.path.join(sample_doc_dir, "company_leave_handbook.md")
            with open(doc_file, "w") as f:
                f.write("""# Acme Corp Employee Leave & Operations Policy

## 1. Annual Paid Leave
All full-time employees are entitled to 20 days of paid annual leave per calendar year. Leaves accrue at the rate of 1.67 days per completed month of service.

## 2. Sick and Medical Leave
Employees may take up to 10 days of paid sick leave annually with medical certification required for absences exceeding 3 consecutive days.

## 3. Remote Work & Security
Remote employees must connect exclusively via the corporate zero-trust network. No organization customer records or database credentials may be stored unencrypted on personal workstations.

## 4. Performance & Travel Reimbursement
Travel expense claims must be submitted within 30 days of trip completion accompanied by itemized receipts.
""")

            doc = Document(
                organization_id=org.id,
                title="Employee Leave & Operations Handbook",
                file_name="company_leave_handbook.md",
                file_type="md",
                file_size=os.path.getsize(doc_file),
                storage_path=doc_file,
                status="PROCESSING"
            )
            db.add(doc)
            await db.commit()

            # 9. Trigger background processing for sample DB schema and document
            await run_schema_discovery_job(sample_source.id)
            await run_document_ingestion_job(doc.id)

def _create_local_demo_sqlite(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            country TEXT NOT NULL,
            annual_spend REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            period TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary REAL NOT NULL
        )
    """)

    # Populate sample rows
    cur.execute("DELETE FROM customers")
    cur.execute("DELETE FROM orders")
    cur.execute("DELETE FROM employees")

    customers_data = [
        (1, "Acme Logistics", "contact@acmelogistics.com", "India", 1450000.0),
        (2, "Global Tech Corp", "billing@globaltech.io", "United States", 3200000.0),
        (3, "Zenith Retail", "accounts@zenithretail.co.uk", "United Kingdom", 980000.0),
        (4, "Nexus Health", "operations@nexushealth.org", "India", 2100000.0),
    ]
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers_data)

    orders_data = [
        (101, 1, "Q3 2026", 450000.0, "COMPLETED", "Supply Chain"),
        (102, 2, "Q3 2026", 1200000.0, "COMPLETED", "Cloud Infrastructure"),
        (103, 3, "Q3 2026", 350000.0, "COMPLETED", "POS Systems"),
        (104, 4, "Q3 2026", 750000.0, "COMPLETED", "Analytics"),
        (105, 1, "Q2 2026", 380000.0, "COMPLETED", "Supply Chain"),
        (106, 2, "Q2 2026", 1050000.0, "COMPLETED", "Cloud Infrastructure"),
    ]
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders_data)

    employees_data = [
        (1, "Alice Morgan", "Engineering", 160000.0),
        (2, "Bob Vance", "Sales", 130000.0),
        (3, "Carol Danvers", "HR", 95000.0),
    ]
    cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", employees_data)

    conn.commit()
    conn.close()
