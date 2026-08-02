from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from api.models.response_models import ApiResponse
from services.partition_service import PartitionService
from api.dependencies import get_partition_service

router = APIRouter()


@router.get("/status", response_model=ApiResponse)
async def get_partition_status(
        service: PartitionService = Depends(get_partition_service)
):
    """دریافت وضعیت پارتیشن‌ها"""
    try:
        result = await service.get_partition_status()
        return ApiResponse(
            message="Partition status",
            data={
                "partitions": result,
                "total": len(result)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{year_month}", response_model=ApiResponse)
async def drop_partition(
        year_month: str,
        service: PartitionService = Depends(get_partition_service)
):
    """
    حذف یک پارتیشن

    - **year_month**: فرمت YYYYMM (مثال: 202401)
    """
    try:
        result = await service.drop_partition(year_month)
        return ApiResponse(
            message=f"Partition {year_month} dropped",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clean", response_model=ApiResponse)
async def clean_old_partitions(
        months: int = Query(6, ge=1, le=24, description="حذف پارتیشن‌های قدیمی‌تر از N ماه"),
        service: PartitionService = Depends(get_partition_service)
):
    """پاکسازی خودکار پارتیشن‌های قدیمی"""
    try:
        result = await service.clean_old_partitions(months)
        return ApiResponse(
            message=f"Cleaned partitions older than {months} months",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))