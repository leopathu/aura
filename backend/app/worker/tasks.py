import asyncio
import logging
from typing import Dict, Any, Optional
from app.core.database import AsyncSessionLocal
from app.documents.ingest_service import IngestionService
from app.models import DataSource, DataSourceCredential, DataSourceSchema, DataSourceTable, DataSourceColumn
from app.connectors.factory import get_data_connector
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def run_document_ingestion_job(document_id: str):
    """Background task for processing document parsing, chunking, and embedding."""
    async with AsyncSessionLocal() as db:
        try:
            await IngestionService.process_document(db, document_id)
            logger.info(f"Successfully processed document {document_id}")
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")

async def run_schema_discovery_job(source_id: str):
    """Background task for inspecting and caching database tables and columns."""
    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(
                select(DataSource, DataSourceCredential)
                .join(DataSourceCredential, DataSourceCredential.data_source_id == DataSource.id)
                .where(DataSource.id == source_id)
            )
            row = res.first()
            if not row:
                return
            source, cred = row

            connector = get_data_connector(source, cred)
            tables_info = await connector.discover_schema()
            await connector.close()

            # Create or update schema
            schema_res = await db.execute(
                select(DataSourceSchema).where(DataSourceSchema.data_source_id == source.id)
            )
            schema = schema_res.scalar_one_or_none()
            if not schema:
                schema = DataSourceSchema(data_source_id=source.id, version=1)
                db.add(schema)
                await db.flush()

            # Clear old tables and insert newly discovered ones
            existing_tables = await db.execute(
                select(DataSourceTable).where(DataSourceTable.schema_id == schema.id)
            )
            for et in existing_tables.scalars().all():
                await db.delete(et)
            await db.flush()

            for t_info in tables_info:
                table_obj = DataSourceTable(
                    schema_id=schema.id,
                    table_name=t_info.table_name,
                    row_count=t_info.row_count,
                    description=f"Discovered table {t_info.table_name}"
                )
                db.add(table_obj)
                await db.flush()

                for c_info in t_info.columns:
                    col_obj = DataSourceColumn(
                        table_id=table_obj.id,
                        column_name=c_info.name,
                        data_type=c_info.data_type,
                        is_nullable=c_info.is_nullable,
                        is_primary_key=c_info.is_primary_key
                    )
                    db.add(col_obj)

            await db.commit()
            logger.info(f"Schema discovery completed for source {source.name} ({len(tables_info)} tables)")
        except Exception as e:
            logger.error(f"Failed schema discovery for source {source_id}: {e}")
