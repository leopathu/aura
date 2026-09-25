from app.models import DataSource, DataSourceCredential
from app.core.crypto import decrypt_secret
from app.connectors.base import DataConnector
from app.connectors.sqlite import SQLiteConnector
from app.connectors.postgres import PostgreSQLConnector
from app.connectors.mysql import MySQLConnector

def get_data_connector(source: DataSource, credential: DataSourceCredential) -> DataConnector:
    connection_uri = decrypt_secret(credential.encrypted_connection_uri)
    source_type = source.type.upper()

    if source_type in ["POSTGRES", "POSTGRESQL"]:
        return PostgreSQLConnector(connection_uri)
    elif source_type in ["MYSQL", "MARIADB"]:
        return MySQLConnector(connection_uri)
    elif source_type in ["SQLITE"]:
        return SQLiteConnector(connection_uri)
    else:
        raise ValueError(f"Unsupported data source type: {source.type}")
