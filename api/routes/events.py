from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional

from api.models.response_models import ApiResponse
from services.event_service import EventService
from api.dependencies import get_event_service

router = APIRouter()

# ✅ استفاده از response_model=None در دکوراتور
@router.get("/count", response_model=None)
async def get_event_count(
    service: EventService = Depends(get_event_service)
):
    """دریافت تعداد کل رویدادها"""
    try:
        count = await service.get_count()
        return ApiResponse(data={"total_events": count})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sample", response_model=None)
async def get_sample_events(
    limit: int = Query(10, ge=1, le=100),
    service: EventService = Depends(get_event_service)
):
    """دریافت نمونه رویدادها"""
    try:
        events = await service.get_sample(limit)
        return ApiResponse(data={"events": events})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=None)
async def get_user_events(
    user_id: int,
    limit: int = Query(20, ge=1, le=1000),
    include_stats: bool = Query(False),
    service: EventService = Depends(get_event_service)
):
    """دریافت رویدادها و آمار یک کاربر"""
    try:
        result = await service.get_user_data(user_id, limit, include_stats)
        return ApiResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=None)
async def search_events(
    query: str,
    limit: int = Query(50, ge=1, le=1000),
    service: EventService = Depends(get_event_service)
):
    """جستجوی پیشرفته با کوئری دلخواه"""
    try:
        # اعتبارسنجی امنیتی کوئری
        if any(keyword in query.upper() for keyword in ["DROP", "DELETE", "UPDATE"]):
            raise HTTPException(status_code=400, detail="Query contains forbidden operations")
        events = await service.search_events(query, limit)
        return ApiResponse(data={"events": events})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))