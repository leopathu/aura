import asyncpg
from typing import List, Dict, Any, Optional
from app.connectors.base import DataConnector, SchemaTableInfo, SchemaColumnInfo

class PostgreSQLConnector(DataConnector):
    def __init__(self, connection_uri: str):
        # Format: postgresql://user:password@host:port/dbname
        self.connection_uri = connection_uri.replace("postgresql+asyncpg://", "postgresql://")
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if not self._pool:
            self._pool = await asyncpg.create_pool(dsn=self.connection_uri, min_size=1, max_size=5)

    async def test_connection(self) -> bool:
        try:
            await self.connect()
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def discover_schema(self) -> List[SchemaTableInfo]:
        await self.connect()
        tables_info: List[SchemaTableInfo] = []

        async with self._pool.acquire() as conn:
            # Query non-system tables
            table_rows = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)

            for trow in table_rows:
                tname = trow["table_name"]
                col_rows = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position;
                """, tname)

                pk_rows = await conn.fetch("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = $1
                      AND tc.constraint_type = 'PRIMARY KEY';
                """, tname)
                pk_set = {r["column_name"] for r in pk_rows}

                columns: List[SchemaColumnInfo] = []
                for c in col_rows:
                    columns.append(
                        SchemaColumnInfo(
                            name=c["column_name"],
                            data_type=c["data_type"],
                            is_nullable=(c["is_nullable"] == "YES"),
                            is_primary_key=(c["column_name"] in pk_set),
                        )
                    )

                # Estimate row count
                try:
                    cnt = await conn.fetchval(f'SELECT COUNT(*) FROM "{tname}"')
                except Exception:
                    cnt = 0

                tables_info.append(SchemaTableInfo(table_name=tname, columns=columns, row_count=cnt or 0))

        return tables_info

    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await self.connect()
        async with self._pool.acquire() as conn:
            # Enforce read only transaction
            async with conn.transaction(readonly=True):
                records = await conn.fetch(sql)
                return [dict(r) for r in records]

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
