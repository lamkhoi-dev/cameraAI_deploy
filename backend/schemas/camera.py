"""Camera request/response schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


class CameraCreate(BaseModel):
    camera_id: str = Field(..., max_length=50, examples=["cam_01"])
    name: str = Field(..., max_length=255, examples=["Sảnh A"])
    location: str = Field(..., max_length=255, examples=["Tầng 1 - Sảnh chính"])
    stream_url: str = Field(..., max_length=500, examples=["rtsp://admin:pass@192.168.1.127:554/Streaming/Channels/101"])
    protocol: str = Field(default="rtsp", pattern="^(rtsp|http|https)$")
    brand: str | None = Field(default=None, examples=["Hikvision"])
    resolution: str | None = Field(default=None, examples=["1920x1080"])
    fps: int = Field(default=25, ge=1, le=60)
    ai_detect_person: bool = True
    ai_detect_vehicle: bool = True
    ai_detect_fire: bool = False
    notes: str | None = None


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    stream_url: str | None = None
    protocol: str | None = None
    brand: str | None = None
    resolution: str | None = None
    fps: int | None = Field(default=None, ge=1, le=60)
    is_active: bool | None = None
    ai_detect_person: bool | None = None
    ai_detect_vehicle: bool | None = None
    ai_detect_fire: bool | None = None
    notes: str | None = None


class AILayerToggle(BaseModel):
    """Toggle AI detection layers for a camera."""
    detect_person: bool | None = None
    detect_vehicle: bool | None = None
    detect_fire: bool | None = None


class CameraResponse(BaseModel):
    id: int
    camera_id: str
    name: str
    location: str
    stream_url: str
    protocol: str
    brand: str | None
    resolution: str | None
    fps: int
    is_active: bool
    connection_status: str
    last_frame_at: datetime | None
    go2rtc_stream_name: str | None
    ai_detect_person: bool
    ai_detect_vehicle: bool
    ai_detect_fire: bool
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CameraTestResult(BaseModel):
    success: bool
    latency_ms: int | None = None
    resolution: str | None = None
    thumbnail_base64: str | None = None
    error: str | None = None


class CameraListResponse(BaseModel):
    cameras: list[CameraResponse]
    total: int
    page: int
    per_page: int
