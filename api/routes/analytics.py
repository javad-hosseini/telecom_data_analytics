# api/routes/analytics.py
# API endpoints for analytics and reporting.
# These endpoints return aggregated data, statistics, and insights.

from fastapi import APIRouter, Depends, Query, HTTPException

from api.dependencies import get_analytics_service
from api.models.response_models import ApiResponse
from services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/top-apps", response_model=None)
async def get_top_apps(
        limit: int = Query(10, ge=1, le=100),
        service: AnalyticsService = Depends(get_analytics_service)
):
    """Get the most used applications ranked by event count"""
    try:
        result = await service.get_top_apps(limit)
        return ApiResponse(
            message=f"Top {limit} applications",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-quality", response_model=None)
async def get_network_quality(
        service: AnalyticsService = Depends(get_analytics_service)
):
    """Get a performance report comparing different network types"""
    try:
        result = await service.get_network_quality()
        return ApiResponse(
            message="Network quality report",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hourly-heatmap", response_model=None)
async def get_hourly_heatmap(
        days: int = Query(7, ge=1, le=30),
        service: AnalyticsService = Depends(get_analytics_service)
):
    """Get event distribution by hour of day for the last N days"""
    try:
        result = await service.get_hourly_heatmap(days)
        return ApiResponse(
            message=f"Hourly distribution for last {days} days",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/device-stats", response_model=None)
async def get_device_stats(
        service: AnalyticsService = Depends(get_analytics_service)
):
    """Get statistics about device types and their performance"""
    try:
        result = await service.get_device_stats()
        return ApiResponse(
            message="Device statistics",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/city-stats", response_model=None)
async def get_city_stats(
        limit: int = Query(10, ge=1, le=50),
        service: AnalyticsService = Depends(get_analytics_service)
):
    """Get statistics about cities with the most traffic"""
    try:
        result = await service.get_city_stats(limit)
        return ApiResponse(
            message=f"Top {limit} cities",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
