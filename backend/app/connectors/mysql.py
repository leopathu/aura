import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import pymysql
from app.connectors.base import DataConnector, SchemaTableInfo, SchemaColumnInfo

class MySQLConnector(DataConnector):
    def __init__(self, connection_uri: str):
        # Format: mysql://user:password@host:port/dbname
        self.connection_uri = connection_uri
        self._parsed = urlparse(connection_uri)

    def _get_connection(self):
        return pymysql.connect(
            host=self._parsed.hostname or "localhost",
            port=self._parsed.port or 3306,
            user=self._parsed.username,
            password=self._parsed.password,
            database=self._parsed.path.lstrip("/"),
            cursorclass=pymysql.cursors.DictCursor,
            read_timeout=30,
            write_timeout=30,
        )

    async def connect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        def _test():
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                conn.close()
                return True
            except Exception:
                return False
        return await asyncio.to_thread(_test)

    async def discover_schema(self) -> List[SchemaTableInfo]:
        def _discover():
            conn = self._get_connection()
            db_name = self._parsed.path.lstrip("/")
            tables_info: List[SchemaTableInfo] = []
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.tables WHERE TABLE_SCHEMA = %s",
                        (db_name,)
                    )
                    tables = cursor.fetchall()
                    for trow in tables:
                        tname = trow["TABLE_NAME"]
                        cursor.execute(
                            """SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY 
                               FROM information_schema.columns 
                               WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
                               ORDER BY ORDINAL_POSITION""",
                            (db_name, tname)
                        )
                        cols = cursor.fetchall()
                        columns = [
                            SchemaColumnInfo(
                                name=c["COLUMN_NAME"],
                                data_type=c["DATA_TYPE"],
                                is_nullable=(c["IS_NULLABLE"] == "YES"),
                                is_primary_key=(c["COLUMN_KEY"] == "PRI"),
                            )
                            for c in cols
                        ]
                        tables_info.append(
                            SchemaTableInfo(
                                table_name=tname,
                                columns=columns,
                                row_count=trow.get("TABLE_ROWS") or 0
                            )
                        )
            finally:
                conn.close()
            return tables_info
        return await asyncio.to_thread(_discover)

    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        def _exec():
            conn = self._get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    return cursor.fetchall()
            finally:
                conn.close()
        return await asyncio.to_thread(_exec)

    async def close(self) -> None:
        pass
