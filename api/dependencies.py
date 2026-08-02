# api/dependencies.py
from functools import lru_cache

from fastapi import Depends

from core.config import get_settings, Settings
from database.clickhouse_client import ClickHouseClient
from repositories.network_event_repository import NetworkEventRepository
from services.analytics_service import AnalyticsService
from services.event_service import EventService
from services.partition_service import PartitionService


# ============ Repository ============
@lru_cache()
def get_repository() -> NetworkEventRepository:
    """ایجاد و کش کردن ریپازیتوری"""
    client = ClickHouseClient.get_instance()
    return NetworkEventRepository(client)


# ============ Services ============

@lru_cache()
def get_event_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> EventService:
    return EventService(repo)


@lru_cache()
def get_analytics_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> AnalyticsService:
    return AnalyticsService(repo)


@lru_cache()
def get_partition_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> PartitionService:
    return PartitionService(repo)


# ============ Settings ============
@lru_cache()
def get_settings() -> Settings:
    """دریافت تنظیمات"""
    return get_settings()
