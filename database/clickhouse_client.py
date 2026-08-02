# database/clickhouse_client.py
import logging
from typing import Optional, Any

import clickhouse_connect

from core.config import get_settings

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """مدیریت اتصال به ClickHouse با استفاده از الگوی Singleton"""

    _instance: Optional['ClickHouseClient'] = None
    _client: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClickHouseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self):
        """برقراری اتصال به ClickHouse"""
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
        """دریافت نمونه Singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def client(self):
        """دریافت کلاینت ClickHouse"""
        if self._client is None:
            self._connect()
        return self._client

    def query(self, query: str) -> Any:
        """اجرای کوئری"""
        try:
            return self.client.query(query)
        except Exception as e:
            logger.error(f"Query error: {e}")
            logger.error(f"Query: {query}")
            raise

    def insert(self, table: str, data: list, column_names: list = None) -> None:
        """درج داده"""
        try:
            self.client.insert(table, data, column_names=column_names)
        except Exception as e:
            logger.error(f"Insert error: {e}")
            raise

    def command(self, command: str) -> Any:
        """اجرای دستور (مانند ALTER)"""
        try:
            return self.client.command(command)
        except Exception as e:
            logger.error(f"Command error: {e}")
            logger.error(f"Command: {command}")
            raise

    def close(self):
        """بستن اتصال"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Closed ClickHouse connection")
