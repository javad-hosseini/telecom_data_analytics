# api/routes/partitions.py
# API endpoints for partition management.
# These endpoints handle viewing and managing table partitions.

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_partition_service
from api.models.response_models import ApiResponse
from services.partition_service import PartitionService

router = APIRouter()


@router.get("/status", response_model=ApiResponse)
async def get_partition_status(
        service: PartitionService = Depends(get_partition_service)
):
    """Get information about all active partitions"""
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
    Delete a specific partition.

    - **year_month**: Format YYYYMM (e.g., 202401 for January 2024)

    WARNING: This permanently deletes all data in that partition!
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
        months: int = Query(6, ge=1, le=24, description="Delete partitions older than N months"),
        service: PartitionService = Depends(get_partition_service)
):
    """
    Automatically delete partitions older than N months.

    Useful for data retention policies - keep only recent data
    and clean up old stuff to save storage.
    """
    try:
        result = await service.clean_old_partitions(months)
        return ApiResponse(
            message=f"Cleaned partitions older than {months} months",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
