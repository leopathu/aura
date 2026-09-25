from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class SchemaColumnInfo:
    def __init__(self, name: str, data_type: str, is_nullable: bool = True, is_primary_key: bool = False):
        self.name = name
        self.data_type = data_type
        self.is_nullable = is_nullable
        self.is_primary_key = is_primary_key

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "is_nullable": self.is_nullable,
            "is_primary_key": self.is_primary_key,
        }

class SchemaTableInfo:
    def __init__(self, table_name: str, columns: List[SchemaColumnInfo], row_count: int = 0):
        self.table_name = table_name
        self.columns = columns
        self.row_count = row_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "row_count": self.row_count,
            "columns": [c.to_dict() for c in self.columns],
        }

class DataConnector(ABC):
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify connectivity."""
        pass

    @abstractmethod
    async def discover_schema(self) -> List[SchemaTableInfo]:
        """Discover database tables and columns."""
        pass

    @abstractmethod
    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read-only query and return records as dictionaries."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        pass
