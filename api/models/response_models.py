from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


# مدل‌های پایه
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


class EventResponse(EventBase):
    """مدل پاسخ برای یک رویداد"""
    pass


# مدل‌های پاسخ
class PaginatedResponse(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=1000)
    total: int
    total_pages: int
    items: List[Any]


class TopAppResponse(BaseModel):
    app_name: str
    event_count: int


class NetworkQualityResponse(BaseModel):
    network_type: str
    avg_latency: float
    avg_packet_loss: float
    avg_speed: float
    total_events: int


class PartitionStatusResponse(BaseModel):
    partition_name: str
    row_count: int
    size_bytes: int
    size_human: str
    min_date: Optional[datetime]
    max_date: Optional[datetime]


class ApiResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)