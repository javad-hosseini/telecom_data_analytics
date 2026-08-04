# api/routes/events.py
# API endpoints for event-related operations.
# These handle requests about events and forward them to the event service.

from fastapi import APIRouter, Depends, Query, HTTPException

from api.dependencies import get_event_service
from api.models.response_models import ApiResponse
from services.event_service import EventService

router = APIRouter()


# response_model=None tells FastAPI not to auto-generate a response model
# We're handling the response format ourselves with ApiResponse

@router.get("/count", response_model=None)
async def get_event_count(
        service: EventService = Depends(get_event_service)
):
    """Get the total number of events in the database"""
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
    """Get a random sample of events. Useful for quick previews."""
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
    """
    Get events and optionally stats for a specific user.

    - user_id: The user's ID (required)
    - limit: Max events to return (default 20, max 1000)
    - include_stats: If true, includes user statistics (default false)
    """
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
    """
    Run a custom search query.

    Security note: Blocks dangerous operations like DROP, DELETE, UPDATE.
    Always adds a LIMIT to prevent huge result sets.
    """
    try:
        # Security check - block destructive operations
        if any(keyword in query.upper() for keyword in ["DROP", "DELETE", "UPDATE"]):
            raise HTTPException(status_code=400, detail="Query contains forbidden operations")
        events = await service.search_events(query, limit)
        return ApiResponse(data={"events": events})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
