# database/clickhouse_client.py
# Manages ClickHouse connection using Singleton pattern

import logging
from typing import Optional, Any

import clickhouse_connect

from core.config import get_settings

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """
    Singleton client for ClickHouse - ensures we only have one connection
    throughout the app. Everywhere that needs DB access uses this instance.
    """

    _instance: Optional['ClickHouseClient'] = None  # the one and only instance
    _client: Optional[Any] = None  # the actual ClickHouse connection

    def __new__(cls):
        # Return existing instance if already created
        if cls._instance is None:
            cls._instance = super(ClickHouseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only connect if we haven't already
        if self._client is None:
            self._connect()

    def _connect(self):
        """Actually connects to ClickHouse and creates the client"""
        try:
            settings = get_settings()

            self._client = clickhouse_connect.get_client(
                host=settings.clickhouse_host,
                port=settings.clickhouse_port,
                username=settings.clickhouse_username,
                password=settings.clickhouse_password,
                database=settings.clickhouse_database,
                secure=settings.clickhouse_secure,
                connect_timeout=settings.connection_timeout,
                send_receive_timeout=settings.query_timeout
            )

            logger.info(f"✅ Connected to ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to ClickHouse: {e}")
            raise

    @classmethod
    def get_instance(cls) -> 'ClickHouseClient':
        """Get the singleton instance, creates it if it doesn't exist"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def client(self):
        """Get the actual ClickHouse client, reconnects if it's gone"""
        if self._client is None:
            self._connect()
        return self._client

    def query(self, query: str) -> Any:
        """Run a simple query and return the result"""
        try:
            return self.client.query(query)
        except Exception as e:
            logger.error(f"Query error: {e}")
            logger.error(f"Query: {query}")
            raise

    def insert(self, table: str, data: list, column_names: list = None) -> None:
        """Insert data into the specified table"""
        try:
            self.client.insert(table, data, column_names=column_names)
        except Exception as e:
            logger.error(f"Insert error: {e}")
            raise

    def command(self, command: str) -> Any:
        """Execute a command like ALTER TABLE"""
        try:
            return self.client.command(command)
        except Exception as e:
            logger.error(f"Command error: {e}")
            logger.error(f"Command: {command}")
            raise

    def close(self):
        """Close the connection if it's open"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Closed ClickHouse connection")
