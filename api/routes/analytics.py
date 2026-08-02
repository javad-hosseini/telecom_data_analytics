from fastapi import APIRouter, Depends, Query, HTTPException
from api.models.response_models import ApiResponse
from services.analytics_service import AnalyticsService
from api.dependencies import get_analytics_service

router = APIRouter()

@router.get("/top-apps", response_model=None)
async def get_top_apps(
    limit: int = Query(10, ge=1, le=100),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """دریافت اپلیکیشن‌های پرمصرف"""
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
    """گزارش کیفیت شبکه‌ها"""
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
    """توزیع ساعتی رویدادها"""
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
    """آمار دستگاه‌ها"""
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
    """آمار شهرها"""
    try:
        result = await service.get_city_stats(limit)
        return ApiResponse(
            message=f"Top {limit} cities",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))