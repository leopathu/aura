import aiosqlite
from typing import List, Dict, Any, Optional
from app.connectors.base import DataConnector, SchemaTableInfo, SchemaColumnInfo

class SQLiteConnector(DataConnector):
    def __init__(self, connection_uri: str):
        # Format: sqlite:///path/to/db or sqlite:////path or just path
        clean_path = connection_uri.replace("sqlite:///", "").replace("sqlite://", "")
        self.db_path = clean_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        if not self._conn:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row

    async def test_connection(self) -> bool:
        try:
            await self.connect()
            cursor = await self._conn.execute("SELECT 1")
            await cursor.fetchone()
            await cursor.close()
            return True
        except Exception:
            return False

    async def discover_schema(self) -> List[SchemaTableInfo]:
        await self.connect()
        tables_info: List[SchemaTableInfo] = []

        cursor = await self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = await cursor.fetchall()
        await cursor.close()

        for (table_name,) in tables:
            # Get columns
            col_cursor = await self._conn.execute(f"PRAGMA table_info({table_name});")
            col_rows = await col_cursor.fetchall()
            await col_cursor.close()

            columns: List[SchemaColumnInfo] = []
            for col in col_rows:
                # cid, name, type, notnull, dflt_value, pk
                columns.append(
                    SchemaColumnInfo(
                        name=col[1],
                        data_type=col[2] or "TEXT",
                        is_nullable=bool(col[3] == 0),
                        is_primary_key=bool(col[5] > 0),
                    )
                )

            # Get row count estimate
            try:
                cnt_cursor = await self._conn.execute(f"SELECT COUNT(*) FROM {table_name};")
                (cnt,) = await cnt_cursor.fetchone()
                await cnt_cursor.close()
            except Exception:
                cnt = 0

            tables_info.append(SchemaTableInfo(table_name=table_name, columns=columns, row_count=cnt))

        return tables_info

    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await self.connect()
        cursor = await self._conn.execute(sql, params or ())
        rows = await cursor.fetchall()
        result = [dict(row) for row in rows]
        await cursor.close()
        return result

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
