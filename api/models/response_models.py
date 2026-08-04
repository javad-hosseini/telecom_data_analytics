# api/models/response_models.py
# Defines the structure of all API responses.
# These are Pydantic models that shape how data looks when it leaves the API.

from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field


# This is the base event model - every event has these fields
class EventBase(BaseModel):
    event_time: datetime
    user_id: int
    event_type: str
    country: str
    city: str
    device: str
    network_type: str
    app_name: str
    latency_ms: int
    download_speed: float
    packet_loss: float


# Used when returning a single event - same as base but with a clearer name
class EventResponse(EventBase):
    """Response model for a single event"""
    pass


# Standard structure for any endpoint that returns a list with pagination
class PaginatedResponse(BaseModel):
    page: int = Field(..., ge=1)  # Current page number (starts at 1)
    page_size: int = Field(..., ge=1, le=1000)  # Items per page
    total: int  # Total items available
    total_pages: int  # Total number of pages
    items: List[Any]  # The actual data for this page


# Used by /api/analytics/top-apps endpoint
class TopAppResponse(BaseModel):
    app_name: str
    event_count: int


# Used by /api/analytics/network-quality endpoint
class NetworkQualityResponse(BaseModel):
    network_type: str
    avg_latency: float
    avg_packet_loss: float
    avg_speed: float
    total_events: int


# Used by /api/partitions/status endpoint
class PartitionStatusResponse(BaseModel):
    partition_name: str  # Like "202401" for January 2024
    row_count: int  # How many events in this partition
    size_bytes: int  # Size in bytes
    size_human: str  # Size in human readable format (like "1.5 GB")
    min_date: Optional[datetime]  # Earliest event in this partition
    max_date: Optional[datetime]  # Latest event in this partition


# This is the wrapper for every API response.
# All endpoints return this structure to keep things consistent.
class ApiResponse(BaseModel):
    status: str = "success"  # "success" or "error"
    message: Optional[str] = None  # Optional human readable message
    data: Optional[Any] = None  # The actual payload (can be anything)
    errors: Optional[List[str]] = None  # List of error messages if something went wrong
    timestamp: datetime = Field(default_factory=datetime.now)  # When the response was generated
