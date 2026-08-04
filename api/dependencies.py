# api/dependencies.py
# Manages dependency injection for the API.
# This is where we tell FastAPI how to create and reuse instances of services.

from functools import lru_cache

from fastapi import Depends

from core.config import get_settings, Settings
from database.clickhouse_client import ClickHouseClient
from repositories.network_event_repository import NetworkEventRepository
from services.analytics_service import AnalyticsService
from services.event_service import EventService
from services.partition_service import PartitionService


# Repository - the data access layer
# @lru_cache() makes sure we only create one instance and reuse it
@lru_cache()
def get_repository() -> NetworkEventRepository:
    """Create and cache the repository instance"""
    client = ClickHouseClient.get_instance()
    return NetworkEventRepository(client)


# Settings - application configuration
@lru_cache()
def get_settings() -> Settings:
    """Get application settings"""
    return get_settings()


# Services - the business logic layer
# Each service depends on the repository (via Depends)

@lru_cache()
def get_event_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> EventService:
    """Create and cache the event service"""
    return EventService(repo)


@lru_cache()
def get_analytics_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> AnalyticsService:
    """Create and cache the analytics service"""
    return AnalyticsService(repo)


@lru_cache()
def get_partition_service(
        repo: NetworkEventRepository = Depends(get_repository)
) -> PartitionService:
    """Create and cache the partition service"""
    return PartitionService(repo)
